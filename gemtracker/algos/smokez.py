"""Smokez reconstruction: mid-curve momentum with asymmetric exits (paper only; docs/algos/smokez.md).

Published (KOL Explorer 90 d): fast-flip, median hold 120 s, median entry mcap $16k, win 38 %.
$16k (~140 SOL) is a fifth of the way up the bonding curve, so he is not sniping launches; he
buys coins that are already moving. A 38 % win rate that is still profitable means small,
frequent losses and a few large winners: a tight stop and a trailing exit, not a fixed target.

  entry  Pump.fun curve coin, past the launch scramble, mcap in a mid-curve band, rising over
         the last minute with several distinct buyers and positive net flow, not too concentrated
  size   moderate, a handful of coins at once
  exit   hard stop (small), partial take-profit, trailing stop once well in profit, time stop

Our adaptation (labelled): the 60 s price-change and buyer counts are measured on the public
feed as received (2.5 s behind); the time stop is longer than his median hold because our fills
land later and winners are what pay. The target's own wallet is never a trigger.
"""
from __future__ import annotations

from ..strategy import Buy
from .swing_base_lib import Tracked


class Smokez(Tracked):
    name = "smokez"
    target_wallet = "5t9xBNuDdGTGpjaPTx6hKd7sdRJbvtKS8Mhq6qVbo8Qz"   # never a trigger
    description = "mid-curve momentum, tight stop, trailing winners (Smokez)"
    venues = ("pump", "launchlab")
    # --- entry filter ---
    min_age_s = 20.0             # past the launch scramble (only coins whose creation we saw)
    max_age_s = 1800.0
    min_entry_mcap_sol = 90.0    # ~$10k
    max_entry_mcap_sol = 400.0   # ~$46k
    min_change_60s = 0.20        # price up >= 20 % over the last minute
    min_buyers_10s = 4
    min_net_sol_60s = 1.0
    max_top10_share = 0.45
    max_dev_sold_frac = 0.5
    max_slippage = 0.25
    # --- sizing / risk ---
    size_frac = 0.08
    max_price_impact = 0.05
    max_exposure_frac = 0.50
    daily_kill_dd = 0.15
    max_positions = 6
    # --- exits ---
    stop_loss = 0.15
    take_profit, tp_fraction = 0.50, 0.5
    trail_arm, trail_drop = 0.30, 0.20
    max_hold_s = 240.0
    retry_after_s = 60.0         # a coin that failed the filter may be re-checked after this

    def __init__(self):
        super().__init__()
        self.last_check: dict[str, int] = self.per_mint({})

    def wants(self, st, now_ms: int) -> bool:
        if not st.seen_create or st.venue not in self.venues or st.migrated:
            return False
        age = st.age_s(now_ms)
        if not (self.min_age_s <= age <= self.max_age_s):
            return False
        if not (self.min_entry_mcap_sol <= st.mcap <= self.max_entry_mcap_sol):
            return False
        if st.dev_bought and st.dev_sold / st.dev_bought > self.max_dev_sold_frac:
            return False
        w60, w10 = st.window(now_ms, 60), st.window(now_ms, 10)
        if not (w60["price_change"] >= self.min_change_60s and w60["net_sol"] >= self.min_net_sol_60s
                and w10["unique_buyers"] >= self.min_buyers_10s):
            return False
        return st.top_holder_share() <= self.max_top10_share   # holder sort last, only with a signal

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        out = self.exits_on_trade(st, now_ms, book)
        if self.is_target(ev):
            return out                  # the target's own trade is never our signal
        if book.has(st.mint) or not st.seen_create:
            return out
        last = self.last_check.get(st.mint)
        if last is not None and now_ms - last < self.retry_after_s * 1000:
            return out
        if self.wants(st, now_ms):
            self.last_check[st.mint] = now_ms
            if self.may_enter(book, now_ms):
                out.append(Buy(st.mint, self.size_sol(book, st), "mid-curve momentum",
                               max_slippage=self.max_slippage))
        elif st.age_s(now_ms) > self.max_age_s:
            self.last_check[st.mint] = now_ms + 10 ** 12   # never again
        return out
