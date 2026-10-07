"""Cupsey reconstruction (scalp_b). Dossier: docs/algos/cupsey.md.

Public: high-frequency launch sniper, ~3 SOL per coin within minutes of launch, flow-based
(no charts), exits in seconds to minutes, 17 s median hold, $10.3k median entry mcap, 42 % win.
Observed (fit span, 2 trips): 2.5 SOL into a 25 s old PumpSwap pool on 3-buyer positive
flow, cut at -24 % after 43 s on all-sell flow; a curve trade sold in 4 chunks within 5 s.
Our adaptation: 2.5 s latency means we hold 60 s not 17 s, size as a fraction of equity
with a 5 % impact cap, fixed stop / trail / flow stop; never acts on Cupsey's own wallet.
"""
from ._scalp_b_base import ScalpBase


class Cupsey(ScalpBase):
    name = "cupsey"
    description = "Launch sniper: fresh pump / PumpSwap coin with positive multi-buyer flow (Cupsey)"
    target_name = "Cupsey"
    target_wallet = "2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f"

    venues = ("pump", "pumpswap")
    max_age_s = 120.0           # observed: minutes after launch
    max_pool_age_s = 120.0      # observed: 25 s after migration
    min_mcap_sol = 40.0         # public $10.3k median entry at ~116 $/SOL ~ 89 SOL
    max_mcap_sol = 400.0

    # entry signal (observed: 3 buyers net +3 SOL in 10 s, +20 % over 60 s)
    sig_secs = 10.0
    sig_min_buyers = 3
    sig_min_net_sol = 0.5
    sig_trend_secs = 60.0
    sig_min_trend = 0.0         # 60 s price change must be positive

    # sizing / risk (our adaptation)
    size_frac = 0.15
    max_exposure_frac = 0.45
    max_positions = 3
    max_loss_per_trade = 0.20
    daily_kill_dd = 0.15

    # exits
    take_profit = 0.25
    take_profit_frac = 0.50
    trail_from_peak = 0.15
    time_stop_s = 60.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy":
            return False
        w = st.window(now_ms, self.sig_secs)
        if w["unique_buyers"] < self.sig_min_buyers or w["net_sol"] < self.sig_min_net_sol:
            return False
        return st.window(now_ms, self.sig_trend_secs)["price_change"] > self.sig_min_trend
