"""Theo reconstruction (paper). Dossier: docs/algos/theo.md.

public: scalper, median hold 17 s, lowest median entry mcap of the group (~$4.8K), WR 0.50.
observed (fit span, 5 trades): one buy at age 4.6 s into a strong launch (35 buys, 15 unique
    buyers / 10 s, +57 % in 10 s), sold in two tranches at 25-28 s when 10 s net flow turned
    negative; one buy at age 203 s on a coin two other elites were already in (n=1).
our adaptation: tight buyer-burst entry; 2-tranche exit (half on flow reversal after 5 s,
    rest on a -15 % 10 s move or the 45 s cap); optional follow-elites branch (never Theo).
"""
from ._scalp_a_base import ScalpBase


class Theo(ScalpBase):
    name = "theo"
    description = "Theo: earliest buyer-burst entry, two-tranche flow-reversal exit, follows other elites"
    target = "Theo"
    target_wallet = "Bi4rd5FH5bYEN8scZ7wevxNZyNmKHdaBcvewdPFxYdLt"
    venues = ("pump",)

    age_min_s = 2.0
    age_max_s = 30.0
    progress_max = 0.6
    min_unique_buyers_10s = 8
    min_buys_10s = 10
    min_net_sol_10s = 0.15
    min_price_change_10s = 0.20
    max_top10_share = 0.30

    follow_elites_min = 2
    follow_age_max_s = 300.0
    follow_min_net_sol_60s = 0.0
    follow_min_price_change_60s = 0.20

    size_frac = 0.12
    hard_stop = 0.25
    tp1_mult = 1.60
    tp1_frac = 0.5
    trail_dd = 0.25
    flow_exit_after_s = 5.0
    flow_exit_frac = 0.5
    flow_exit_price_change_10s = -0.15
    time_stop_s = 45.0
