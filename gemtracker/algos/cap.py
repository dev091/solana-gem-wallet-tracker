"""Cap reconstruction (scalp_b). Dossier: docs/algos/cap.md.

Public: fast-flip, 59 s median hold, $17.6k median entry mcap (~152 SOL, i.e. the last
quarter of the bonding curve or a fresh PumpSwap pool), win rate unpublished, recent
7-day drawdown. Observed (fit span): no Cap trades yet. Unknown: his trigger; the late-curve
entry reads as a migration / breakout play: buy strength near the all-time high.
Our adaptation: 120 s hold, fraction-of-equity sizing with a 5 % impact cap, -15 % stop,
trail / flow stop; never acts on Cap's own wallet.
"""
from ._scalp_b_base import ScalpBase


class Cap(ScalpBase):
    name = "cap"
    description = "Late-curve / migration breakout: near ATH with broad, positive flow (Cap)"
    target_name = "Cap"
    target_wallet = "CAPn1yH4oSywsxGU456jfgTrSSUidf9jgeAnHceNUJdw"

    venues = ("pump", "pumpswap")
    max_age_s = 3600.0          # late curve: age is not the filter, progress is
    min_progress = 0.55
    max_pool_age_s = 120.0
    min_mcap_sol = 100.0
    max_mcap_sol = 400.0
    min_holders = 30
    max_top10 = 0.35

    # entry signal (unknown; breakout heuristic)
    sig_secs = 60.0
    sig_min_buyers = 15
    sig_min_net_sol = 3.0
    sig_ath_frac = 0.90         # mcap within 10 % of its ATH
    sig_fast_secs = 10.0        # and the last 10 s are net positive

    # sizing / risk (our adaptation)
    size_frac = 0.15
    max_exposure_frac = 0.45
    max_positions = 3
    max_loss_per_trade = 0.15
    daily_kill_dd = 0.15

    # exits
    take_profit = 0.30
    take_profit_frac = 0.50
    trail_from_peak = 0.15
    time_stop_s = 120.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy" or st.ath_mcap <= 0 or st.mcap < self.sig_ath_frac * st.ath_mcap:
            return False
        w = st.window(now_ms, self.sig_secs)
        if w["unique_buyers"] < self.sig_min_buyers or w["net_sol"] < self.sig_min_net_sol:
            return False
        return st.window(now_ms, self.sig_fast_secs)["net_sol"] > 0
