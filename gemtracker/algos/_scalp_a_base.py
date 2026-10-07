"""Shared state machine for the scalp_a reconstructions (Decu, Cented, Trunoest, Theo).

Paper only. One parameterised template; every trader module only sets class attributes.
Labels used in the per-trader docs: public (published stats), observed (fit-span tape),
our adaptation (changes forced by our 2.5 s latency / $100 book), unknown.

State machine (per coin):
    idle -> [entry filter on a trade we did not make] -> pending buy -> held
    held -> [take-profit tranche | flow reversal | trailing stop | hard stop | time stop] -> flat
Risk rules (class attributes): hard stop per trade, daily drawdown kill switch (no new
entries for the rest of the UTC day), max concurrent positions and max exposure share.
Sizing: a fraction of current equity (cash + marked positions), capped so the buy moves
the curve price by at most `max_impact` (exact constant-product maths, see impact_cap).

The target elite's own trades are never a signal: an event whose user is the target wallet
is ignored, and the target's name is removed from the "other elites in" set.
"""
from __future__ import annotations

import math
import random
from collections import deque

from ..papersim import buy_out
from ..strategy import Buy, Sell, Strategy

DAY_MS = 86_400_000


def impact_cap(rq: int, rb: int, fee_bps: int, max_impact: float) -> float:
    """Largest SOL spend whose constant-product fill lifts the price by at most max_impact.

    After a buy of net SOL n on reserves (rq, rb) the price is (rq+n)^2/(rq*rb), so the
    move is (1+n/rq)^2-1; invert and add the venue fee back. Checked against buy_out in tests.
    """
    if rq <= 0 or rb <= 0:
        return 0.0
    net = rq / 1e9 * (math.sqrt(1.0 + max_impact) - 1.0)
    return net / (1.0 - fee_bps / 10_000)


def price_after_buy(sol: float, fee_bps: int, rq: int, rb: int) -> float:
    """Marginal price (SOL per token) after spending `sol`, via the simulator's buy_out."""
    tokens, fee = buy_out(sol, fee_bps, rq, rb)
    if tokens <= 0:
        return 0.0
    return ((rq + (sol - fee) * 1e9) / 1e9) / ((rb - tokens * 1e6) / 1e6)


class ScalpBase(Strategy):
    name = "base"                 # subclasses set a unique name
    target = ""                   # elite name being reconstructed (its wallet is never a signal)
    target_wallet = ""

    # ----- universe -----
    venues = ("pump",)
    require_seen_create = True    # age is only exact for coins whose create we recorded
    allow_mayhem = False
    age_min_s = 2.0
    age_max_s = 30.0
    progress_max = 0.6
    mcap_min_sol = 0.0            # SOL; 0 disables
    mcap_max_sol = 0.0

    # ----- entry signal (10 s window = what a scalper sees on the trade feed) -----
    min_unique_buyers_10s = 6
    min_buys_10s = 6
    min_net_sol_10s = 0.1
    min_price_change_10s = 0.0
    min_buy_sell_ratio_10s = 1.5
    max_top10_share = 0.40
    min_holders = 0
    dev_sold_blocks = True        # no entry once the creator has sold any tokens
    follow_elites_min = 0         # >0: alternative entry when this many OTHER elites are in
    follow_age_max_s = 300.0
    follow_min_net_sol_60s = 0.0
    follow_min_price_change_60s = 0.0
    dip_mode = False              # Decu-observed: buy a migrated coin after a flush
    dip_from_ath = 0.4            # price at least this far below ATH
    dip_min_sell_sol_60s = 5.0
    dip_max_age_s = 900.0

    # ----- sizing and risk -----
    size_frac = 0.12              # of current equity, per entry
    dip_size_frac = 0.06
    max_impact = 0.05             # a buy may lift the price by at most this
    max_slippage = 0.25
    max_positions = 4
    max_exposure_frac = 0.60      # cost basis of open positions / equity
    hard_stop = 0.15              # sell all when price <= entry * (1 - hard_stop)
    daily_kill_dd = 0.20          # no new entries after losing this share of day-start equity
    cooldown_s = 120.0            # per coin, after a trip or a rejected buy
    min_entry_gap_s = 0.0         # global: no new entry this soon after the last Buy (elite cadence)
    max_entries_per_coin = 2

    # ----- exits -----
    tp1_mult = 1.25               # first take-profit, as a multiple of the fill price
    tp1_frac = 1.0                # fraction sold at tp1 (1.0 = single exit)
    trail_dd = 0.20               # after tp1 (or from entry when tp1_frac < 1): sell rest at this drop from peak
    flow_exit_after_s = 5.0       # flow-reversal exit active after this hold
    flow_exit_net_sol_10s = 0.0   # ... when 10 s net flow is below this
    flow_exit_price_change_10s = -0.08  # ... and 10 s price change below this
    flow_exit_frac = 1.0
    time_stop_s = 30.0
    entry_mode = "signal"         # signal | random (baseline: same universe, random entry)
    random_entry_p = 0.02
    random_seed = 7

    def __init__(self):
        self.pos = {}       # mint -> dict(entry, peak, opened, sold_frac, tp_done)
        self.selling = {}   # mint -> (decision_ms, why, frac): a Sell we submitted, not yet filled
        self.tried = {}     # mint -> (count, last_rx)
        self.day_start = None   # (utc day, equity)
        self.killed_day = None
        self.last_entry_ms = -10 ** 12
        self.rng = random.Random(self.random_seed)
        self.decisions = deque(maxlen=1000)  # (now_ms, side, mint) for tests
        self.sell_timeout_x = 3  # give up waiting for a Sell fill after this many latencies

    # ----- helpers -----
    def other_elites(self, st) -> set:
        return {n for _, n, _ in st.elite_buys if n != self.target}

    def _equity(self, book, market) -> float:
        try:
            return book.equity_sol(market)
        except Exception:
            return book.cash_sol

    def _day_guard(self, book, market, now_ms) -> bool:
        """True when new entries are allowed today. Rolled from on_tick every second so the
        day-start equity is the equity at the day boundary, not at the first candidate."""
        day = now_ms // DAY_MS
        if self.day_start is None or self.day_start[0] != day:
            self.day_start = (day, self._equity(book, market))
        if self.killed_day == day:
            return False
        if self._equity(book, market) <= self.day_start[1] * (1 - self.daily_kill_dd):
            self.killed_day = day
            return False
        return True

    def _exposure(self, book) -> float:
        return sum(p.cost_sol for p in book.positions.values()) + book.pending_buy_sol()

    def _universe_ok(self, st, now_ms) -> bool:
        if st.venue not in self.venues or not st.reserve_quote or st.price <= 0:
            return False
        if st.mayhem and not self.allow_mayhem:
            return False
        return True

    def _fresh_ok(self, st, now_ms) -> bool:
        if self.require_seen_create and not st.seen_create:
            return False
        age = st.age_s(now_ms)
        if not (self.age_min_s <= age <= self.age_max_s) or st.progress > self.progress_max:
            return False
        if st.migrated:
            return False
        mc = st.mcap
        if self.mcap_min_sol and mc < self.mcap_min_sol:
            return False
        if self.mcap_max_sol and mc > self.mcap_max_sol:
            return False
        if self.dev_sold_blocks and st.dev_sold > 0:
            return False
        w10 = st.window(now_ms, 10)   # cached per event; still only after the cheap gates
        if w10["unique_buyers"] < self.min_unique_buyers_10s or w10["buys"] < self.min_buys_10s:
            return False
        if w10["net_sol"] < self.min_net_sol_10s or w10["price_change"] < self.min_price_change_10s:
            return False
        if w10["buys"] < self.min_buy_sell_ratio_10s * max(1, w10["sells"]):
            return False
        # holder statistics last: they sort every balance, so only coins with real flow pay
        if st.holder_count() < self.min_holders or st.top_holder_share() > self.max_top10_share:
            return False
        return True

    def _follow_ok(self, st, now_ms) -> bool:
        if not self.follow_elites_min or len(self.other_elites(st)) < self.follow_elites_min:
            return False
        if self.require_seen_create and not st.seen_create:
            return False
        if st.age_s(now_ms) > self.follow_age_max_s or st.migrated or st.progress > 0.97:
            return False
        w60 = st.window(now_ms, 60)
        return (w60["net_sol"] >= self.follow_min_net_sol_60s
                and w60["price_change"] >= self.follow_min_price_change_60s)

    def _dip_ok(self, st, now_ms) -> bool:
        if not self.dip_mode or not st.migrated or st.ath_mcap <= 0:
            return False
        if st.age_s(now_ms) > self.dip_max_age_s or st.mcap > st.ath_mcap * (1 - self.dip_from_ath):
            return False
        w60 = st.window(now_ms, 60)
        return w60["sell_sol"] >= self.dip_min_sell_sol_60s and w60["net_sol"] < 0

    def entry_reason(self, st, now_ms) -> str:
        """Which entry branch fires (empty string = none). Pure function of state before now."""
        if not self._universe_ok(st, now_ms):
            return ""
        if self.entry_mode == "random":
            age = st.age_s(now_ms)
            if self.age_min_s <= age <= self.age_max_s and not st.migrated \
                    and self.rng.random() < self.random_entry_p:
                return "random"
            return ""
        if self._fresh_ok(st, now_ms):
            return "fresh-launch flow"
        if self._follow_ok(st, now_ms):
            return "other elites in"
        if self._dip_ok(st, now_ms):
            return "post-migration flush"
        return ""

    def size_sol(self, st, book, market, frac: float) -> float:
        eq = self._equity(book, market)
        want = eq * frac
        if self._exposure(book) + want > eq * self.max_exposure_frac:
            want = eq * self.max_exposure_frac - self._exposure(book)
        cap = impact_cap(st.reserve_quote, st.reserve_base, st.fee_bps, self.max_impact)
        return max(0.0, min(want, cap, book.free_sol() - 0.001))

    # ----- callbacks -----
    def on_trade(self, st, ev, now_ms, book):
        if ev.user and ev.user == self.target_wallet:
            return []                      # the target's own trade is never our signal
        out = self._exits_for(st, now_ms, book)
        if out:
            return out
        if st.mint in book.positions or book.has(st.mint):
            return []
        if len(book.positions) + len(book.pending) >= self.max_positions:
            return []
        n, last = self.tried.get(st.mint, (0, -10 ** 12))
        if n >= self.max_entries_per_coin or now_ms - last < self.cooldown_s * 1000:
            return []
        if now_ms - self.last_entry_ms < self.min_entry_gap_s * 1000:
            return []
        reason = self.entry_reason(st, now_ms)
        if not reason:
            return []
        market = self._market_of(book)
        if not self._day_guard(book, market, now_ms):
            return []
        frac = self.dip_size_frac if reason == "post-migration flush" else self.size_frac
        sol = self.size_sol(st, book, market, frac)
        if sol < 0.005:
            return []
        self.tried[st.mint] = (n + 1, now_ms)
        self.last_entry_ms = now_ms
        self.decisions.append((now_ms, "buy", st.mint))
        return [Buy(st.mint, sol, f"{self.target}: {reason}", max_slippage=self.max_slippage)]

    def on_tick(self, market, now_ms, book):
        self._set_market(book, market)
        self._day_guard(book, market, now_ms)   # roll the day (and the kill switch) on the clock
        self._prune_gone(market, book)
        out = []
        for mint in list(book.positions):
            st = market.get(mint)
            if st is not None:
                out += self._exits_for(st, now_ms, book)
        return out

    def on_fill(self, fill, book):
        if fill.side == "buy":
            if fill.status == "filled":
                px = fill.price or getattr(fill, "exec_price", 0.0)
                p = self.pos.setdefault(fill.mint, {"entry": px, "peak": px,
                                                     "opened": fill.arrival_ms, "tp_done": False})
                p["peak"] = max(p["peak"], px)
            return
        self.selling.pop(fill.mint, None)
        p = self.pos.get(fill.mint)
        if p is not None and fill.status == "filled" and fill.mint in book.positions:
            p["tp_done"] = True   # a partial exit filled: the remainder trails from here
        if fill.mint not in book.positions:
            self.pos.pop(fill.mint, None)
            n, _ = self.tried.get(fill.mint, (1, 0))
            self.tried[fill.mint] = (n, fill.arrival_ms)

    # ----- exits -----
    def _sell_in_flight(self, st, now_ms, book) -> bool:
        """True while a Sell we submitted may still fill. PaperSim can drop a Sell without a
        fill callback, so after `sell_timeout_x` latencies we stop waiting and decide again."""
        rec = self.selling.get(st.mint)
        if rec is None:
            return False
        pending = getattr(book, "pending", None) or ()
        if any(isinstance(q.intent, Sell) and q.intent.mint == st.mint for q in pending):
            return True
        cfg = getattr(book, "cfg", None)
        lat = cfg.venue_latency_ms.get(st.venue, cfg.latency_ms) if cfg is not None else 2500
        if now_ms - rec[0] <= self.sell_timeout_x * lat:
            return True
        del self.selling[st.mint]   # dropped by the simulator: never filled, never rejected
        return False

    def _exits_for(self, st, now_ms, book):
        mint = st.mint
        p = self.pos.get(mint)
        if p is None or mint not in book.positions or st.price <= 0:
            return []
        if self._sell_in_flight(st, now_ms, book):
            return []
        if p["entry"] <= 0:
            p["entry"] = p["peak"] = st.price   # unknown fill price: measure from here
        p["peak"] = max(p["peak"], st.price)
        mult = st.price / p["entry"]
        held = (now_ms - p["opened"]) / 1000
        frac, why = 0.0, ""
        if mult <= 1 - self.hard_stop:
            frac, why = 1.0, "hard stop"
        elif held >= self.time_stop_s:
            frac, why = 1.0, "time stop"
        elif not p["tp_done"] and mult >= self.tp1_mult:
            frac, why = self.tp1_frac, "take profit"
        elif (p["tp_done"] or self.tp1_frac < 1) and st.price <= p["peak"] * (1 - self.trail_dd):
            frac, why = 1.0, "trailing stop"
        elif held >= self.flow_exit_after_s:
            w10 = st.window(now_ms, 10)
            if w10["net_sol"] < self.flow_exit_net_sol_10s \
                    and w10["price_change"] < self.flow_exit_price_change_10s:
                frac, why = (1.0 if p["tp_done"] else self.flow_exit_frac), "flow reversal"
        if not frac:
            return []
        # tp_done is set in on_fill when the tranche actually fills (a dropped Sell must not
        # leave the position stuck without its take-profit / stop)
        self.selling[mint] = (now_ms, why, frac)
        self.decisions.append((now_ms, "sell", mint))
        return [Sell(mint, frac, f"{self.target}: {why}")]

    def _prune_gone(self, market, book):
        """Drop per-mint memory for coins the market forgot and the book no longer holds."""
        for d in (self.tried, self.selling, self.pos):
            gone = [m for m in d if market.get(m) is None and not book.has(m)]
            for m in gone:
                del d[m]

    # market handle for equity marks (PaperSim does not pass it to on_trade)
    def _set_market(self, book, market):
        book._market = market

    def _market_of(self, book):
        return getattr(book, "_market", None)
