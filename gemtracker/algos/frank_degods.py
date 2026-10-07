"""Frank degods reconstruction: post-migration swing (paper only; docs/algos/frank_degods.md).

Published (KOL Explorer 90 d): swing, median hold 9,360 s (2.6 h), median entry mcap $497k.
Public record (Lookonchain, FOMO leaderboards, DL News): early entries into coins that then
run, adds on dips of conviction holds, and fast block selling when the market turns. $497k
(~4,300 SOL) is well past migration, so his coins trade on PumpSwap with an established holder
base; a 2.6 h hold is a swing on flow, not a scalp.

  entry  migrated coin (PumpSwap) in a mid-cap band with sustained inflow over the last minute
         (many distinct buyers, positive net SOL, price rising), broad holder base
  size   concentrated: few, larger positions
  adds   on a dip while flow stays positive (observed publicly; blocked by papersim, see docs)
  exit   wide stop, partial take-profit at 2x, trailing once >= +60 %, flow-breakdown exit,
         3 h time stop

Our adaptation (labelled): PumpSwap orders land 5.5 s after the decision; the mcap band is a
sanity band in SOL at a fixed SOL/USD; the breakdown exit uses received 60 s net flow. The
target's own wallet is never a trigger.
"""
from __future__ import annotations

from ..strategy import Buy, Sell
from .swing_base_lib import Tracked


class FrankDegods(Tracked):
    name = "frank_degods"
    target_wallet = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"   # never a trigger
    description = "post-migration swing on sustained flow, concentrated, hours-long (Frank degods)"
    venues = ("pumpswap",)
    # --- entry filter ---
    min_entry_mcap_sol = 1500.0    # ~$175k
    max_entry_mcap_sol = 12000.0   # ~$1.4M; also a sanity cap for mis-scaled PumpSwap pools
    min_buyers_60s = 8
    min_net_sol_60s = 3.0
    min_change_60s = 0.03
    min_trades_seen = 40           # established tape history for this coin
    min_holders = 60               # approximate (holders seen since first observation)
    max_top10_share = 0.35
    max_slippage = 0.15
    # --- sizing / risk ---
    size_frac = 0.20
    max_price_impact = 0.05
    max_exposure_frac = 0.60
    daily_kill_dd = 0.15
    max_positions = 3
    # --- exits ---
    stop_loss = 0.30
    take_profit, tp_fraction = 1.00, 0.5
    trail_arm, trail_drop = 0.60, 0.30
    max_hold_s = 3 * 3600.0
    breakdown_net_sol_60s = -5.0   # exit under water when a minute of heavy net selling arrives
    add_on_dip = False             # public behaviour; papersim refuses a Buy while a position is open
    retry_after_s = 30.0

    def __init__(self):
        super().__init__()
        self.last_check: dict[str, int] = self.per_mint({})

    def wants(self, st, now_ms: int) -> bool:
        if st.venue not in self.venues or not st.migrated:
            return False
        if not (self.min_entry_mcap_sol <= st.mcap <= self.max_entry_mcap_sol):
            return False
        if st.n_buys + st.n_sells < self.min_trades_seen:
            return False
        w = st.window(now_ms, 60)
        if not (w["unique_buyers"] >= self.min_buyers_60s and w["net_sol"] >= self.min_net_sol_60s
                and w["price_change"] >= self.min_change_60s):
            return False
        # holder statistics last: they sort every balance of a migrated coin
        return st.holder_count() >= self.min_holders and st.top_holder_share() <= self.max_top10_share

    def exit_for(self, mint, price, now_ms):
        s = super().exit_for(mint, price, now_ms)
        if s is not None:
            return s
        p = self.pos.get(mint)
        st = self.market.get(mint) if self._market() is not None else None
        if p and st is not None and price < p["entry"]:
            if st.window(now_ms, 60)["net_sol"] <= self.breakdown_net_sol_60s:
                return Sell(mint, 1.0, "flow breakdown")
        return None

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        out = self.exits_on_trade(st, now_ms, book)
        if self.is_target(ev):
            return out                  # the target's own trade is never our signal
        if book.has(st.mint) or st.venue not in self.venues or not st.migrated:
            return out                  # not our universe: remember nothing about it
        last = self.last_check.get(st.mint)
        if last is not None and now_ms - last < self.retry_after_s * 1000:
            return out
        self.last_check[st.mint] = now_ms
        if self.wants(st, now_ms) and self.may_enter(book, now_ms):
            out.append(Buy(st.mint, self.size_sol(book, st), "migrated flow", max_slippage=self.max_slippage))
        return out
