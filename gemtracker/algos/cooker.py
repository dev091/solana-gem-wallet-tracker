"""Cooker (@CookerFlips) reconstruction (scalp_b). Dossier: docs/algos/cooker.md.

Public: fastest scalper on the board, 9 s median hold, $6.3k median entry mcap (~54 SOL,
i.e. the first fifth of the bonding curve), 71 % win rate, thin margins on volume.
Observed (fit span): no Cooker trades yet. Unknown: his actual trigger; we assume the
only thing visible 9 s after launch is the first burst of buyers and the dev's behaviour.
Our adaptation: hold 25 s not 9 s, tight +20 % / -12 % brackets, fraction-of-equity sizing
with a 5 % impact cap; never acts on Cooker's own wallet.
"""
from ._scalp_b_base import ScalpBase


class Cooker(ScalpBase):
    name = "cooker"
    description = "Launch burst scalper: brand-new pump coin, many buyers in 5 s, dev not selling (Cooker)"
    target_name = "Cooker"
    target_wallet = "8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6"

    venues = ("pump",)
    require_create = True       # exact age is the whole point
    max_age_s = 30.0
    min_mcap_sol = 35.0
    max_mcap_sol = 120.0
    max_top10 = 0.50
    max_dev_sold_frac = 0.0     # any dev sale disqualifies

    # entry signal (unknown; burst heuristic)
    sig_secs = 5.0
    sig_min_buyers = 4
    sig_flow_secs = 10.0
    sig_min_net_sol = 0.5

    # sizing / risk (our adaptation)
    size_frac = 0.12
    max_exposure_frac = 0.36
    max_positions = 3
    max_loss_per_trade = 0.12
    daily_kill_dd = 0.12

    # exits
    take_profit = 0.20
    take_profit_frac = 1.0      # thin-margin flip: all out at target
    trail_from_peak = 0.10
    trail_arm = 0.08
    time_stop_s = 25.0
    flow_stop_secs = 5.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy":
            return False
        if st.window(now_ms, self.sig_secs)["unique_buyers"] < self.sig_min_buyers:
            return False
        return st.window(now_ms, self.sig_flow_secs)["net_sol"] >= self.sig_min_net_sol
