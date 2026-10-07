"""Mr. Frog reconstruction: launch-window flip (paper only; see docs/algos/mr_frog.md).

Published (KOL Explorer 90 d): fast-flip, median hold 120 s, median entry mcap $4.2k, win 93.5 %.
$4.2k is the Pump.fun launch mcap (~30-40 SOL), so the entry is within the first seconds of a
coin's life, before any pump. A 93.5 % win rate on 120 s holds says he sells into the first
wave of buyers rather than waiting for a top. Decision logic kept recognisable:

  entry  a coin he saw launch, seconds old, still at launch mcap, with the first few distinct
         buyers already in and the dev not selling
  size   small, many coins
  exit   into the first wave of followers (observed: sold 5.7 s after entry while 6 other
         buyers were still arriving), else first pop (take-profit), hard stop, 120 s time stop

Observed on our tape (2026-10-07 17 UTC, 442 s): 3 buys, 2 round trips, fixed 3 SOL stake on
launch-block coins (his buy is the first trade we receive; ~10 % of the launch reserves), one
0.05 SOL probe; trips +16 % in 43 s and +11 % in 5.7 s. He is the first wave, we cannot be.

Our adaptation (labelled): every intent fills 2.5 s after the decision, so entry needs real
early flow (>= min_buyers_10s) instead of being first; max_slippage is widened because launch
prices gap; the "wave over" exit sells when 10 s net flow stops, which is what his 6 s exit
looks like from the outside. The target's own wallet is never a trigger.
"""
from __future__ import annotations

from ..strategy import Buy, Sell
from .swing_base_lib import Tracked


class MrFrog(Tracked):
    name = "mr_frog"
    description = "launch-window flip: new coin, first buyers in, sell the first pop (Mr. Frog)"
    target_wallet = "4DdrfiDHpmx55i4SPssxVzS9ZaKLb8qr45NKY9Er9nNh"   # never a trigger
    venues = ("pump", "launchlab")
    # --- entry filter (observed-launch coins only) ---
    max_age_s = 20.0            # seconds since creation at decision
    max_entry_mcap_sol = 60.0   # ~$7k at $116; launch is ~30 SOL
    min_buyers_10s = 3          # distinct buyers in the last 10 s (our adaptation for latency)
    min_net_sol_10s = 0.3       # net SOL inflow in the last 10 s
    max_dev_sold_frac = 0.0     # dev has not sold any of its own buy
    allow_mayhem = False
    max_slippage = 0.40         # our adaptation: launch prices gap; still rejects runaway fills
    # --- sizing / risk ---
    size_frac = 0.04
    max_price_impact = 0.05
    max_exposure_frac = 0.40
    daily_kill_dd = 0.15
    max_positions = 8
    # --- exits ---
    take_profit, tp_fraction = 0.35, 1.0
    stop_loss = 0.25
    max_hold_s = 120.0
    fade_after_s = 6.0          # observed: exit into the follower wave, seconds after entry
    fade_net_sol_10s = 0.0      # 10 s net flow at or below this = the wave is over, sell

    def __init__(self):
        super().__init__()
        self.skipped: set[str] = self.per_mint(set())

    def wants(self, st, now_ms: int) -> bool:
        if not st.seen_create or st.venue not in self.venues or st.migrated:
            return False
        if st.mayhem and not self.allow_mayhem:
            return False
        if st.age_s(now_ms) > self.max_age_s or st.mcap > self.max_entry_mcap_sol:
            return False
        if st.dev_bought and st.dev_sold / st.dev_bought > self.max_dev_sold_frac:
            return False
        w = st.window(now_ms, 10)
        return w["unique_buyers"] >= self.min_buyers_10s and w["net_sol"] >= self.min_net_sol_10s

    def exit_for(self, mint, price, now_ms):
        s = super().exit_for(mint, price, now_ms)
        if s is not None:
            return s
        p, m = self.pos.get(mint), self._market()
        st = m.get(mint) if m is not None else None
        if p and st is not None and now_ms - p["opened"] >= self.fade_after_s * 1000                 and st.window(now_ms, 10)["net_sol"] <= self.fade_net_sol_10s:
            return Sell(mint, 1.0, f"wave over {price / p['entry'] - 1:+.0%}")
        return None

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        out = self.exits_on_trade(st, now_ms, book)
        if self.is_target(ev):
            return out                  # the target's own trade is never our signal
        if st.mint in self.skipped or book.has(st.mint):
            return out
        if st.seen_create and st.age_s(now_ms) > self.max_age_s:
            self.skipped.add(st.mint)
            return out
        if self.wants(st, now_ms) and self.may_enter(book, now_ms):
            self.skipped.add(st.mint)   # one attempt per coin
            out.append(Buy(st.mint, self.size_sol(book, st), "launch flow", max_slippage=self.max_slippage))
        return out
