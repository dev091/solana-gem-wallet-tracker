"""Cented reconstruction (paper). Dossier: docs/algos/cented.md.

public: "7-second trader", ~845 trades/day, 62 % WR, median hold 7-12 s, median entry ~$5.9K.
observed (fit span, 35 trades, all pump curve): enters at age 3-11 s, progress 0.2-0.32,
    6-7 unique buyers / 10 s; 0.06 or 2.9 SOL first clip then a fixed 0.244 SOL add ladder
    and scale-out sells (first partial when the 10 s flow turns negative).
our adaptation: single clip (PaperSim drops adds on a held coin), 2-tranche exit:
    60 % at +25 %, remainder trails 25 % from peak; flow-reversal exit after 5 s; 60 s cap.
"""
from ._scalp_a_base import ScalpBase


class Cented(ScalpBase):
    name = "cented"
    description = "Cented: very early curve entry on buyer bursts, scale-out with trailing remainder"
    target = "Cented"
    target_wallet = "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o"
    venues = ("pump",)

    age_min_s = 2.0
    age_max_s = 20.0
    progress_max = 0.5
    min_unique_buyers_10s = 5
    min_buys_10s = 6
    min_net_sol_10s = 0.1
    min_price_change_10s = 0.0
    max_top10_share = 0.45

    size_frac = 0.10
    hard_stop = 0.20
    tp1_mult = 1.25
    tp1_frac = 0.6
    trail_dd = 0.25
    flow_exit_after_s = 5.0
    flow_exit_frac = 0.5
    time_stop_s = 60.0
    max_positions = 5
