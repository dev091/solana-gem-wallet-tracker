"""Decu reconstruction (paper). Dossier: docs/algos/decu.md; measured behaviour:
data/history/elite_trades/dossiers/Decu.md (3,529 real DEV round trips, 2026-08-08..09-04).

public: scalper, median hold 14 s, median entry mcap ~$8.2K (~70 SOL at $116), WR 0.64.
measured (DEV, Slinky21 + Kaggle, n=3,510 closed trips): pump curve only (no PumpSwap buys
    at all), entry mcap p25-p75 49-107 SOL, coin age p50 12 s (82 % <= 120 s), progress
    p50 0.56, one position at a time, 126 trips/day, hold p50 34 s (p75 75 s), realised
    mult p50 1.06, WR 0.60, exits ~0.64 of the hold's peak. Enters into a live buyer burst:
    10 s before the buy p25 13 unique buyers / 14 buys / net +0.4 SOL; the dev has already
    sold in 68 % of entries, so a dev sale is not a veto.
our adaptation: same universe and flow gates at ~p25 of what he saw (our fill arrives
    2.5 s late); hard stop 0.28 (his p10 realised mult 0.73), partial take-profit at 1.5x
    with a 0.30 trail (he gives back a third of the peak), 75 s time stop (his p75 hold).
    The old post-migration "dip" branch was built on 6 trades and is dropped: he never
    buys on PumpSwap in the data.
"""
from ._scalp_a_base import ScalpBase


class Decu(ScalpBase):
    name = "decu"
    description = "Decu: fresh-launch buyer-burst scalp at 35-150 SOL mcap, one position, ~1 min hold"
    target = "Decu"
    target_wallet = "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9"
    venues = ("pump",)

    age_min_s = 2.0
    age_max_s = 120.0
    progress_max = 0.85
    mcap_min_sol = 35.0
    mcap_max_sol = 150.0
    min_unique_buyers_10s = 14
    min_buys_10s = 14
    min_net_sol_10s = 2.0
    min_price_change_10s = 0.0
    min_buy_sell_ratio_10s = 1.2
    min_holders = 10
    max_top10_share = 0.50
    dev_sold_blocks = False

    dip_mode = False

    size_frac = 0.15
    max_positions = 1
    max_exposure_frac = 0.30
    min_entry_gap_s = 100.0
    hard_stop = 0.28
    tp1_mult = 1.50
    tp1_frac = 0.5
    trail_dd = 0.30
    flow_exit_after_s = 10.0
    time_stop_s = 75.0
