"""Shared skeleton for the scalp_b reconstructions (Cupsey, Cooker, Trenchman, Cap).

Not an algo itself (name "base" is skipped by the loader). Each trader module subclasses
ScalpBase, sets its universe / risk / exit parameters as class attributes and overrides
`signal_ok` with its own entry logic. Everything a decision reads is state already received
at `now_ms`; nothing here looks at later rows.

Risk rules common to the group (Rahul's addendum, labelled "our adaptation"):
  sizing      every entry is `size_frac` of current equity (cash + marked positions), so
              profits compound; capped so the buy moves the curve price <= `max_impact`
  hard stop   `max_loss_per_trade` below the fill price -> sell everything
  kill switch no new entries for the rest of the UTC day once equity is `daily_kill_dd`
              below the day-start equity; exits keep running
  exposure    open cost + pending buys <= `max_exposure_frac` of equity, `max_positions` coins
  target      the reconstruction never acts on its own target wallet's trades
  quote       coins quoted in anything but SOL are skipped (their "SOL" figures are wrong)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..chain_events import WSOL
from ..papersim import buy_out
from ..strategy import Buy, Sell, Strategy

DAY_MS = 86_400_000


@dataclass
class Trip:
    opened_ms: int
    entry_price: float
    peak: float
    tranche_done: bool = False


def liquidity_cap(st, max_impact: float) -> float:
    """Largest SOL spend that moves the constant-product price by at most `max_impact`."""
    rq, rb, fee = st.reserve_quote, st.reserve_base, st.fee_bps
    if rq <= 0 or rb <= 0:
        return 0.0
    net = rq * (math.sqrt(1 + max_impact) - 1)          # price ~ (rq + net)^2 / k
    sol = net / 1e9 / max(1e-9, 1 - fee / 10_000)
    tokens, _ = buy_out(sol, fee, rq, rb)                 # verify with the exact fill maths
    if tokens <= 0:
        return 0.0
    after = (rq + (sol * (1 - fee / 10_000)) * 1e9) / (rb - tokens * 1e6) if rb > tokens * 1e6 else math.inf
    before = rq / rb
    if after / before - 1 > max_impact * 1.01:            # numeric guard, shrink a little
        sol *= 0.98
    return sol


class ScalpBase(Strategy):
    name = "base"
    target_name = ""
    target_wallet = ""

    # ---- universe (what the trader even looks at) ----
    venues = ("pump",)
    require_create = False      # only coins whose creation we saw (exact age)
    min_age_s = 0.0
    max_age_s = 120.0
    max_pool_age_s = 120.0      # pumpswap: seconds since the first pool trade we saw
    min_mcap_sol = 0.0
    max_mcap_sol = 1e9
    min_progress = 0.0
    max_top10 = 1.0
    max_dev_sold_frac = 1.0     # 1.0 = don't care
    min_holders = 0

    # ---- sizing and risk (our adaptation) ----
    size_frac = 0.10
    max_impact = 0.05
    max_exposure_frac = 0.50
    max_positions = 5
    max_loss_per_trade = 0.20
    daily_kill_dd = 0.15
    cooldown_s = 120.0
    max_slippage = 0.25

    # ---- exits ----
    take_profit = 0.30
    take_profit_frac = 0.50
    trail_from_peak = 0.15
    trail_arm = 0.10            # trailing stop is live once the peak is this far above entry
    time_stop_s = 60.0
    flow_stop_secs = 10.0
    flow_stop_ratio = 2.0       # sells >= ratio * buys and net flow < 0 -> dump exit
    flow_stop_min_s = 3.0

    def __init__(self):
        self.market = None
        self.trips: dict[str, Trip] = {}
        self.cooldown: dict[str, int] = {}
        self.non_sol: set[str] = set()
        self.pool_rx: dict[str, int] = {}
        self.day = None
        self.day_eq = 0.0
        self.killed = False
        self.n_universe = 0     # diagnostics for the baseline (random entry on the same universe)
        self.n_signals = 0

    # ------------------------------------------------------------------ hooks
    def on_tick(self, market, now_ms, book):
        self.market = market
        self._roll_day(now_ms, book)
        self._prune_gone(market, book)
        out = []
        for mint in list(book.positions):
            st = market.get(mint)
            if st is not None:
                out += self._exits(st, now_ms, book)
        return out

    def on_trade(self, st, ev, now_ms, book):
        if ev.quote_mint and ev.quote_mint != WSOL:
            self.non_sol.add(st.mint)
            return []
        if st.venue == "pumpswap" and st.mint not in self.pool_rx:
            self.pool_rx[st.mint] = now_ms
        if ev.user and ev.user == self.target_wallet:
            return []                      # reconstruct, never copy
        if st.mint in book.positions:
            return self._exits(st, now_ms, book)
        if book.has(st.mint):
            return []
        return self._entry(st, ev, now_ms, book)

    def on_fill(self, fill, book):
        if fill.side == "buy":
            if fill.status == "filled":
                px = fill.price or getattr(fill, "exec_price", 0.0)
                self.trips[fill.mint] = Trip(fill.arrival_ms, px, px)
            else:
                self.cooldown[fill.mint] = fill.arrival_ms
        elif fill.mint not in book.positions:
            self.trips.pop(fill.mint, None)
            self.cooldown[fill.mint] = fill.arrival_ms
        elif fill.status == "filled":
            t = self.trips.get(fill.mint)
            if t is not None and (fill.reason == "take" or fill.mint in book.positions):
                t.tranche_done = True      # the tranche really sold; set here, not at submit

    def _prune_gone(self, market, book):
        """Forget coins the market dropped that we neither hold nor have an order on."""
        for c in (self.cooldown, self.non_sol, self.pool_rx, self.trips):
            gone = [m for m in c if market.get(m) is None and not book.has(m)]
            for m in gone:
                c.discard(m) if isinstance(c, set) else c.pop(m, None)

    # ------------------------------------------------------------------ entry
    def universe_ok(self, st, now_ms) -> bool:
        """Full universe test (cheap gates, then holder statistics)."""
        return self._universe_cheap(st, now_ms) and self._holders_ok(st)

    def _universe_cheap(self, st, now_ms) -> bool:
        if st.venue not in self.venues or st.mint in self.non_sol:
            return False
        if self.require_create and not st.seen_create:
            return False
        if st.venue == "pumpswap":
            age = (now_ms - self.pool_rx.get(st.mint, now_ms)) / 1000
            if age > self.max_pool_age_s:
                return False
        else:
            age = st.age_s(now_ms)
            if not (self.min_age_s <= age <= self.max_age_s):
                return False
            if st.progress < self.min_progress:
                return False
        mcap = st.mcap
        if not (self.min_mcap_sol <= mcap <= self.max_mcap_sol):
            return False
        if self.max_dev_sold_frac < 1.0 and st.dev_bought and st.dev_sold / st.dev_bought > self.max_dev_sold_frac:
            return False
        return True

    def _holders_ok(self, st) -> bool:
        """Holder statistics sort every balance: checked last, only for coins with a signal."""
        if self.min_holders and st.holder_count() < self.min_holders:
            return False
        if self.max_top10 < 1.0 and st.top_holder_share() > self.max_top10:
            return False
        return True

    def signal_ok(self, st, ev, now_ms) -> bool:
        """The trader's own trigger; subclasses override."""
        return False

    def _entry(self, st, ev, now_ms, book):
        last = self.cooldown.get(st.mint)
        if last is not None and now_ms - last < self.cooldown_s * 1000:
            return []
        if not self._universe_cheap(st, now_ms):
            return []
        self.n_universe += 1          # coins past the cheap gates (holder stats come after the signal)
        if not self.signal_ok(st, ev, now_ms):
            return []
        if not self._holders_ok(st):
            return []
        self.n_signals += 1
        sol = self.size(st, now_ms, book)
        if sol <= 0:
            return []
        return [Buy(st.mint, sol, f"{self.name} entry", max_slippage=self.max_slippage)]

    # ------------------------------------------------------------------ risk
    def equity(self, book) -> float:
        if self.market is not None:
            return book.equity_sol(self.market)
        return book.cash_sol + sum(p.cost_sol for p in book.positions.values())

    def _roll_day(self, now_ms, book):
        day = now_ms // DAY_MS
        eq = self.equity(book)
        if day != self.day:
            self.day, self.day_eq, self.killed = day, eq, False
        elif not self.killed and self.day_eq > 0 and eq < self.day_eq * (1 - self.daily_kill_dd):
            self.killed = True

    def size(self, st, now_ms, book) -> float:
        """SOL to spend now, or 0 if a risk rule forbids a new entry."""
        if self.killed or len(book.positions) + len(book.pending) >= self.max_positions:
            return 0.0
        eq = self.equity(book)
        exposure = sum(p.cost_sol for p in book.positions.values()) + book.pending_buy_sol()
        room = self.max_exposure_frac * eq - exposure
        sol = min(self.size_frac * eq, room, liquidity_cap(st, self.max_impact), book.free_sol() - book.cfg.tx_fee_sol)
        return sol if sol >= book.cfg.min_order_sol else 0.0

    # ------------------------------------------------------------------ exits
    def _trip(self, mint, book) -> Trip | None:
        t = self.trips.get(mint)
        if t is None:
            pos = book.positions.get(mint)
            if pos is None or pos.tokens <= 0:
                return None
            t = self.trips[mint] = Trip(pos.opened_ms, pos.cost_sol / pos.tokens, pos.cost_sol / pos.tokens)
        return t

    def _exits(self, st, now_ms, book):
        if any(isinstance(p.intent, Sell) and p.intent.mint == st.mint for p in book.pending):
            return []
        t = self._trip(st.mint, book)
        if t is None or st.price <= 0:
            return []
        if t.entry_price <= 0:
            t.entry_price = t.peak = st.price   # unknown fill price: measure from here
        t.peak = max(t.peak, st.price)
        held = (now_ms - t.opened_ms) / 1000
        up = st.price / t.entry_price - 1
        if up <= -self.max_loss_per_trade:
            return [Sell(st.mint, 1.0, "stop")]
        if held >= self.flow_stop_min_s:
            w = st.window(now_ms, self.flow_stop_secs)
            if w["sells"] >= self.flow_stop_ratio * max(1, w["buys"]) and w["net_sol"] < 0:
                return [Sell(st.mint, 1.0, "flow")]
        if not t.tranche_done and up >= self.take_profit:
            return [Sell(st.mint, self.take_profit_frac, "take")]   # tranche_done set on the fill
        if t.peak >= t.entry_price * (1 + self.trail_arm) and st.price <= t.peak * (1 - self.trail_from_peak):
            return [Sell(st.mint, 1.0, "trail")]
        if held >= self.time_stop_s:
            return [Sell(st.mint, 1.0, "time")]
        return []
