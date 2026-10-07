"""Decu reconstruction (paper). Dossier: docs/algos/decu.md.

public: scalper, median hold 14 s, median entry mcap ~$8.2K (~70 SOL at $116), WR 0.64.
observed (fit span, n=6 trades): all on PumpSwap, buying migrated coins 44-58 % below ATH
    into heavy selling (net60 ~ -41 SOL), holding ~16 s, one sell per trip.
our adaptation: fresh-launch flow entry on the pump curve at his published mcap band plus
    a half-size "post-migration flush" branch for the observed behaviour; 30 s time stop
    instead of 14 s because our fill arrives 2.5 s (pump) / 5.5 s (pumpswap) late.
"""
from ._scalp_a_base import ScalpBase


class Decu(ScalpBase):
    name = "decu"
    description = "Decu: fresh-launch flow scalp at ~70 SOL mcap; half-size post-migration flush buys"
    target = "Decu"
    target_wallet = "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9"
    venues = ("pump", "pumpswap")

    age_min_s = 3.0
    age_max_s = 45.0
    progress_max = 0.6
    mcap_min_sol = 35.0
    mcap_max_sol = 150.0
    min_unique_buyers_10s = 6
    min_buys_10s = 6
    min_net_sol_10s = 0.3
    min_price_change_10s = 0.10
    max_top10_share = 0.35

    dip_mode = True
    dip_from_ath = 0.40
    dip_min_sell_sol_60s = 10.0
    dip_max_age_s = 1800.0

    size_frac = 0.15
    dip_size_frac = 0.07
    hard_stop = 0.15
    tp1_mult = 1.25
    tp1_frac = 1.0
    flow_exit_after_s = 5.0
    time_stop_s = 30.0
