"""Trenchman reconstruction (scalp_b). Dossier: docs/algos/trenchman.md.

Public: fast-flip, 60 s median hold, $7.7k median entry mcap (~66 SOL, mid bonding curve),
win rate unpublished; larger single trades than the scalpers (4.71 SOL sell seen in feed).
Observed (fit span): no Trenchman trades yet. Unknown: his trigger; the mid-curve entry
with a 60 s hold reads as "join a curve that is already running with a broad holder base".
Our adaptation: 120 s hold (60 s elite + latency margin), fraction-of-equity sizing with a
5 % impact cap, trail / stop / flow stop; never acts on Trenchman's own wallet.
"""
from ._scalp_b_base import ScalpBase


class Trenchman(ScalpBase):
    name = "trenchman"
    description = "Mid-curve momentum flip: broad holder base, strong 60 s flow and price (Trenchman)"
    target_name = "Trenchman"
    target_wallet = "Hw5UKBU5k3YudnGwaykj5E8cYUidNMPuEewRRar5Xoc7"

    venues = ("pump", "launchlab")
    min_age_s = 15.0
    max_age_s = 180.0
    min_mcap_sol = 45.0
    max_mcap_sol = 150.0
    min_holders = 15
    max_top10 = 0.45
    max_dev_sold_frac = 0.50

    # entry signal (unknown; momentum heuristic)
    sig_secs = 60.0
    sig_min_buyers = 10
    sig_min_net_sol = 1.0
    sig_min_trend = 0.20

    # sizing / risk (our adaptation)
    size_frac = 0.15
    max_exposure_frac = 0.45
    max_positions = 3
    max_loss_per_trade = 0.20
    daily_kill_dd = 0.15

    # exits
    take_profit = 0.40
    take_profit_frac = 0.50
    trail_from_peak = 0.20
    time_stop_s = 120.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy":
            return False
        w = st.window(now_ms, self.sig_secs)
        return (w["unique_buyers"] >= self.sig_min_buyers and w["net_sol"] >= self.sig_min_net_sol
                and w["price_change"] >= self.sig_min_trend)
