"""Shared plumbing for the swing_base group (Mr. Frog, Smokez, Frank degods) and the baselines.

`Tracked` remembers each position only from the simulator's fills (entry price, open time,
peak price, exit stage), never from intents, so an algo's exit logic sees exactly what it
could know: its own fills and the coin state as received. No Strategy subclass lives here, so
live.py / replay.py do not load this module as an algo.
"""
from __future__ import annotations

import hashlib

from ..strategy import Sell, Strategy


def unit_hash(*parts: object) -> float:
    """Deterministic uniform in [0, 1) from the parts (order-independent reproducibility)."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2 ** 64


class Tracked(Strategy):
    """Position memory from fills plus a parameterised exit ladder.

    Exit parameters (class attributes, all optional):
      stop_loss      fraction below entry that closes the whole position (0.25 = -25 %)
      take_profit    fraction above entry that sells `tp_fraction` of the position once
      tp_fraction    share sold at take_profit (1.0 closes the position)
      trail_arm      gain from entry after which a trailing stop is armed (None = off)
      trail_drop     drop from the peak price that closes the position once armed
      max_hold_s     time stop from the fill's arrival, seconds (None = off)
    """
    stop_loss: float | None = None
    take_profit: float | None = None
    tp_fraction: float = 1.0
    trail_arm: float | None = None
    trail_drop: float | None = None
    max_hold_s: float | None = None

    target_wallet: str = ""          # the trader being reconstructed; never a trigger

    def __init__(self):
        self.pos: dict[str, dict] = {}
        self._per_mint: list = [self.pos]   # per-mint containers pruned when a coin is gone

    def per_mint(self, container):
        """Register a per-mint dict/set so on_tick forgets coins the market dropped."""
        self._per_mint.append(container)
        return container

    def _prune_gone(self, market, book) -> None:
        has = getattr(book, "has", None)
        for c in self._per_mint:
            gone = [m for m in c if market.get(m) is None and not (has and has(m))]
            for m in gone:
                c.discard(m) if isinstance(c, set) else c.pop(m, None)

    def is_target(self, ev) -> bool:
        """True for the reconstructed trader's own trade (an empty wallet matches nothing)."""
        return bool(self.target_wallet) and ev.user == self.target_wallet

    # ----- fills -----
    def on_fill(self, fill, book) -> None:
        if fill.status != "filled":
            return
        if fill.side == "buy":
            cur = self.pos.get(fill.mint)
            if cur is None:
                px = fill.price or getattr(fill, "exec_price", 0.0)
                self.pos[fill.mint] = {"entry": px, "opened": fill.arrival_ms,
                                       "peak": px, "stage": 0}
        elif fill.mint not in book.positions:
            self.pos.pop(fill.mint, None)
        else:
            p = self.pos.get(fill.mint)
            if p is not None and (fill.reason.startswith("take-profit") or fill.mint in book.positions):
                p["stage"] = 1          # the tranche really sold; set here, not at submit

    # ----- exits -----
    def exit_for(self, mint: str, price: float, now_ms: int) -> Sell | None:
        """The exit intent (if any) for a tracked position at `price`, decided at now_ms."""
        p = self.pos.get(mint)
        if p is None or price <= 0 or p["entry"] <= 0:
            return None
        if price > p["peak"]:
            p["peak"] = price
        gain = price / p["entry"] - 1
        if self.stop_loss is not None and gain <= -self.stop_loss:
            return Sell(mint, 1.0, f"stop {gain:+.0%}")
        if self.trail_arm is not None and self.trail_drop is not None and p["peak"] / p["entry"] - 1 >= self.trail_arm:
            if price <= p["peak"] * (1 - self.trail_drop):
                return Sell(mint, 1.0, f"trail {gain:+.0%} from peak {p['peak'] / p['entry'] - 1:+.0%}")
        if self.take_profit is not None and p["stage"] == 0 and gain >= self.take_profit:
            return Sell(mint, self.tp_fraction, f"take-profit {gain:+.0%}")   # stage set on the fill
        if self.max_hold_s is not None and now_ms - p["opened"] >= self.max_hold_s * 1000:
            return Sell(mint, 1.0, f"time stop {gain:+.0%}")
        return None

    def exits_on_trade(self, st, now_ms: int, book) -> list:
        if st.mint in book.positions:
            s = self.exit_for(st.mint, st.price, now_ms)
            return [s] if s else []
        return []

    def exits_on_tick(self, market, now_ms: int, book) -> list:
        out = []
        for mint in list(book.positions):
            st = market.get(mint)
            if st is None:
                continue
            s = self.exit_for(mint, st.price, now_ms)
            if s:
                out.append(s)
        return out

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        return self.exits_on_trade(st, now_ms, book)


    # ----- sizing and risk (Rahul's addendum: compound, liquidity cap, explicit risk rules) -----
    size_frac: float = 0.05          # of current equity per entry (of the start stake if not compounding)
    compound: bool = True            # size from equity = cash + marked positions (baselines: False)
    max_price_impact: float | None = 0.05   # no buy may move the price more than this
    max_exposure_frac: float | None = None  # open cost + pending buys <= this share of equity
    daily_kill_dd: float | None = None      # no new entries for the UTC day after this drawdown
    max_positions: int | None = None        # own cap on concurrent positions (sim caps at 10)

    def _market(self):
        return getattr(self, "market", None)

    def equity_sol(self, book) -> float:
        m = self._market()
        return book.equity_sol(m) if (m is not None and self.compound) else (
            book.cash_sol if self.compound else book.start_sol)

    def liquidity_cap_sol(self, st, want: float) -> float:
        """Largest spend <= want whose constant-product fill moves the price <= max_price_impact."""
        if self.max_price_impact is None or not st.reserve_quote or not st.reserve_base:
            return want
        from ..papersim import buy_out
        rq, rb = st.reserve_quote, st.reserve_base

        def impact(sol: float) -> float:
            tokens, fee = buy_out(sol, st.fee_bps, rq, rb)
            if rb <= tokens * 1e6:
                return float("inf")
            return ((rq + (sol - fee) * 1e9) / (rb - tokens * 1e6)) / (rq / rb) - 1

        if impact(want) <= self.max_price_impact:
            return want
        lo, hi = 0.0, want
        for _ in range(24):            # bisection on an increasing impact curve
            mid = (lo + hi) / 2
            if impact(mid) <= self.max_price_impact:
                lo = mid
            else:
                hi = mid
        return lo

    def size_sol(self, book, st=None) -> float:
        want = self.equity_sol(book) * self.size_frac
        return self.liquidity_cap_sol(st, want) if st is not None else want

    def _roll_day(self, book, now_ms: int) -> float:
        """Roll the UTC day (start-of-day equity, halt flag) and update the kill switch.
        Called every tick so the day-start equity is the equity at the day boundary."""
        day = now_ms // 86_400_000
        eq = self.equity_sol(book)
        if getattr(self, "_day", None) != day:
            self._day, self._sod_equity, self._halted = day, eq, False
        if self.daily_kill_dd is not None and not self._halted and self._sod_equity > 0 \
                and eq <= self._sod_equity * (1 - self.daily_kill_dd):
            self._halted = True
        return eq

    def may_enter(self, book, now_ms: int) -> bool:
        """Risk gates: daily kill switch, exposure cap, position cap."""
        eq = self._roll_day(book, now_ms)
        if self._halted:
            return False
        if self.max_positions is not None and len(book.positions) + len(book.pending) >= self.max_positions:
            return False
        if self.max_exposure_frac is not None:
            exposed = sum(p.cost_sol for p in book.positions.values()) + book.pending_buy_sol()
            if exposed >= eq * self.max_exposure_frac:
                return False
        return True

    def on_tick(self, market, now_ms: int, book) -> list:
        self.market = market      # the state as received so far; used only for marks
        self._roll_day(book, now_ms)
        self._prune_gone(market, book)
        return self.exits_on_tick(market, now_ms, book)
