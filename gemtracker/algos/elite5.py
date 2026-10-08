"""Five autonomous elite-style algos (2026-10-07), built from each trader's measured profile.

Source: data/history/elite_trades/stats_<Name>.json (their own trips, 2026-08-08..09-04 ET).
Each algo takes only the slice of that trader's own book that was profitable for HIM AND is
the least sensitive to our 2.5-4 s latency: older coins, longer holds, no launch sniping
(dossiers show every launch-snipe slice is lost 3 s after his fill).

Nothing here reads any elite or follower wallet as a signal; `target_wallet` only makes the
trader's own trade a non-trigger (reconstruct, never copy). Paper only. NOT validated: these
are hypotheses from the elites' conditional stats (selection bias: we see the coins they chose),
running in the live paper book to be measured, not delivered.
"""
from ._scalp_b_base import ScalpBase

NO_FLOW_STOP = 1e9   # flow_stop_ratio that never fires (dip buyers enter on sell flow)


def ath_ratio(st) -> float:
    return st.mcap / st.ath_mcap if st.ath_mcap > 0 else 1.0


class _Elite5(ScalpBase):
    name = "base"
    venues = ("pump",)
    size_frac = 0.20            # of equity: compounding from $100
    max_exposure_frac = 0.60
    max_positions = 3
    max_impact = 0.03
    daily_kill_dd = 0.15        # no new entries for the rest of the ET day
    cooldown_s = 600.0


class FrogDip(_Elite5):
    """Mr. Frog: his win rate is 84-87 % at every coin age past 2 min and 94 % below 40 SOL mcap.
    He buys stale, low-mcap curve coins in a quiet moment, below their high (price/ATH p50 0.73,
    10 s buys p50 0), and sells into the next push. Our trigger: a sell into a quiet, older coin."""
    name = "frog_dip"
    description = "Mr. Frog style: dip-buy quiet older curve coins below their high, 28-60 SOL"
    target_name = "Mr. Frog"
    target_wallet = "4DdrfiDHpmx55i4SPssxVzS9ZaKLb8qr45NKY9Er9nNh"
    min_age_s, max_age_s = 180.0, 6 * 3600.0
    min_mcap_sol, max_mcap_sol = 28.0, 60.0
    max_top10 = 0.45
    take_profit, take_profit_frac = 0.20, 1.0
    trail_arm, trail_from_peak = 0.12, 0.08
    max_loss_per_trade = 0.15
    time_stop_s = 1800.0
    flow_stop_ratio = NO_FLOW_STOP

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "sell" or not 0.40 <= ath_ratio(st) <= 0.85:
            return False
        if st.window(now_ms, 10.0)["buys"] > 2:
            return False
        return -0.20 <= st.window(now_ms, 60.0)["price_change"] <= 0.0


class CookerOld(_Elite5):
    """Cooker: his launch snipes lose (-103 SOL at age <= 30 s); his buys on coins aged 2 min-1 h
    win 79-92 %. Fast flip on a fresh buy burst in an older coin."""
    name = "cooker_old"
    description = "Cooker style, older coins only: buy burst on a 2-60 min old curve coin, quick flip"
    target_name = "Cooker"
    target_wallet = "8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6"
    min_age_s, max_age_s = 120.0, 3600.0
    min_mcap_sol, max_mcap_sol = 35.0, 150.0
    max_top10 = 0.45
    max_dev_sold_frac = 0.5
    take_profit, take_profit_frac = 0.12, 1.0
    trail_arm, trail_from_peak = 0.06, 0.06
    max_loss_per_trade = 0.10
    time_stop_s = 45.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy":
            return False
        w = st.window(now_ms, 10.0)
        return (w["unique_buyers"] >= 6 and w["net_sol"] >= 1.0
                and st.window(now_ms, 60.0)["price_change"] >= 0.05)


class TrunoestHold(_Elite5):
    """Trunoest: his 1-30 min holds carry his book (WR 70-84 %, +506 SOL); 40-90 SOL mcap and
    coins 30 s-10 min old are his profitable bands. Momentum entry, let it run."""
    name = "trunoest_hold"
    description = "Trunoest style: strong-flow 40-90 SOL curve coin aged 30 s-10 min, hold up to 30 min"
    target_name = "Trunoest"
    target_wallet = "ardinRsN1mNYVeoJWTBsWeYeXvuR9UUDGMsCDKpb6AT"
    min_age_s, max_age_s = 30.0, 600.0
    min_mcap_sol, max_mcap_sol = 40.0, 90.0
    max_top10 = 0.40
    max_dev_sold_frac = 0.5
    take_profit, take_profit_frac = 0.50, 0.5
    trail_arm, trail_from_peak = 0.20, 0.20
    max_loss_per_trade = 0.20
    time_stop_s = 1800.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy":
            return False
        w = st.window(now_ms, 10.0)
        return (w["unique_buyers"] >= 14 and w["net_sol"] >= 2.0
                and st.window(now_ms, 60.0)["price_change"] >= 0.25)


class TheoHold(_Elite5):
    """Theo: below 60 SOL mcap he is profitable, and his 1-30 min holds win 55-62 %."""
    name = "theo_hold"
    description = "Theo style: flow entry on a 28-60 SOL curve coin aged 30-120 s, hold up to 15 min"
    target_name = "Theo"
    target_wallet = "Bi4rd5FH5bYEN8scZ7wevxNZyNmKHdaBcvewdPFxYdLt"
    min_age_s, max_age_s = 30.0, 120.0
    min_mcap_sol, max_mcap_sol = 28.0, 60.0
    max_top10 = 0.40
    max_dev_sold_frac = 0.5
    take_profit, take_profit_frac = 0.40, 0.5
    trail_arm, trail_from_peak = 0.20, 0.20
    max_loss_per_trade = 0.20
    time_stop_s = 900.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy":
            return False
        w = st.window(now_ms, 10.0)
        return (w["unique_buyers"] >= 8 and w["net_sol"] >= 1.0
                and st.window(now_ms, 60.0)["price_change"] >= 0.15)


class CentedHold(_Elite5):
    """Cented: 4,781 closed trips; profitable below 90 SOL, still positive at 30-120 s coin age,
    and his 5-30 min holds win 62 %. Near-high continuation entry."""
    name = "cented_hold"
    description = "Cented style: near-high continuation on a 28-90 SOL coin aged 30-120 s, hold up to 10 min"
    target_name = "Cented"
    target_wallet = "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o"
    min_age_s, max_age_s = 30.0, 120.0
    min_mcap_sol, max_mcap_sol = 28.0, 90.0
    max_top10 = 0.40
    max_dev_sold_frac = 0.5
    take_profit, take_profit_frac = 0.30, 0.5
    trail_arm, trail_from_peak = 0.15, 0.15
    max_loss_per_trade = 0.18
    time_stop_s = 600.0

    def signal_ok(self, st, ev, now_ms) -> bool:
        if ev.side != "buy" or ath_ratio(st) < 0.85:
            return False
        w = st.window(now_ms, 10.0)
        pc = st.window(now_ms, 60.0)["price_change"]
        return w["unique_buyers"] >= 10 and w["net_sol"] >= 1.0 and 0.10 <= pc <= 1.0
