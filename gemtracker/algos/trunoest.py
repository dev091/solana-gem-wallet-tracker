"""Trunoest reconstruction (paper). Dossier: docs/algos/trunoest.md.

public: scalper, median hold 21 s (longest of the group), median entry ~$7.4K, WR 0.62;
    Kolscan #1 over 30 days (+$755K, WR 60 %). No other public information.
observed (fit span): no trades recorded yet; everything below is unknown / template.
our adaptation: the group's "public-only" template: launch-flow entry at his mcap band with
    a holder-count floor (slightly later, more confirmed entries than Cented/Theo), single
    exit at +30 %, -15 % stop, flow reversal, 40 s cap (2x his published hold).
"""
from ._scalp_a_base import ScalpBase


class Trunoest(ScalpBase):
    name = "trunoest"
    description = "Trunoest: confirmed-launch flow scalp (holder floor), single exit, 40 s cap"
    target = "Trunoest"
    target_wallet = "ardinRsN1mNYVeoJWTBsWeYeXvuR9UUDGMsCDKpb6AT"
    venues = ("pump",)

    age_min_s = 5.0
    age_max_s = 60.0
    progress_max = 0.7
    mcap_min_sol = 40.0
    mcap_max_sol = 200.0
    min_unique_buyers_10s = 6
    min_buys_10s = 6
    min_net_sol_10s = 0.2
    min_price_change_10s = 0.05
    min_holders = 10
    max_top10_share = 0.35

    size_frac = 0.12
    hard_stop = 0.15
    tp1_mult = 1.30
    tp1_frac = 1.0
    flow_exit_after_s = 6.0
    time_stop_s = 40.0
