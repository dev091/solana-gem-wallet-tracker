"""Regression tests for the code-review fixes on the paper algos (one per defect).

1 bounded per-mint state   2 exit state set at fill, not submit   3 holder stats after cheap gates
4 target wallet never a trigger   5/6 elite-copy matches the elite's own event, leader set at fill
7 day-start equity rolls at the day start   8 zero entry price never divides
"""
import unittest
from collections import deque
from types import SimpleNamespace

import test_algos_scalp_a as A
import test_algos_scalp_b as B
import test_algos_swing_base as S
from gemtracker import chain_events as ce
from gemtracker.algos.baselines import BaseEliteCopy, BaseHold60, BaseRandom
from gemtracker.algos.cap import Cap
from gemtracker.algos.cupsey import Cupsey
from gemtracker.algos.decu import Decu
from gemtracker.algos.frank_degods import FrankDegods
from gemtracker.algos.mr_frog import MrFrog
from gemtracker.algos.smokez import Smokez
from gemtracker.algos.swing_base_lib import Tracked
from gemtracker.algos._scalp_b_base import Trip
from gemtracker.market import Market
from gemtracker.papersim import Fill, PaperSim, Position, SimConfig
from gemtracker.strategy import Buy, Sell

DAY = 86_400_000
LAT = 1000


def book_for(strat, latency=LAT):
    sim = PaperSim([strat], SimConfig(latency_ms=latency, venue_latency_ms={}), lambda: 100.0)
    return sim.books[strat.name]


def hold(book, mint, tokens=1000.0, cost=0.1, opened=0):
    book.positions[mint] = Position(mint, tokens=tokens, cost_sol=cost, opened_ms=opened)


def boom(*_a, **_k):
    raise AssertionError("holder stats computed before the cheap gates")


def fill(side, mint, status="filled", reason="", t=0, price=1.0):
    return Fill("x", side, mint, t, t + LAT, status, reason, price=price, exec_price=price)


def market_with_launch(mint="M", n=12):
    m = Market()
    rows, rq, rb = A.launch(mint, n=n)
    st = None
    for rx, ev in rows:
        st = m.apply(ev, rx)
    return m, st, rq, rb, rows[-1][0]


class BoundedStateTest(unittest.TestCase):
    """1: per-mint memory is dropped once the coin left the market and the book."""

    def check(self, strat, containers, market_mint="HELD"):
        m = Market()
        m._token(market_mint, 0)
        book = book_for(strat)
        hold(book, "HELD")
        for c in containers:
            for mint in ("GONE", "HELD", "SEEN"):
                if isinstance(c, set):
                    c.add(mint)
                else:
                    c[mint] = (1, 0) if strat.__class__.__module__.endswith("_scalp_a_base") else 0
        strat.on_tick(m, 10_000, book)
        for c in containers:
            self.assertNotIn("GONE", c)
            self.assertIn("HELD", c)                     # held: keep even when the market forgot it

    def test_scalp_a_tried_pruned_and_decisions_bounded(self):
        s = Decu()
        s.tried = {}
        s.tried.update({"GONE": (1, 0), "HELD": (1, 0)})
        m, book = Market(), book_for(s)
        hold(book, "HELD")
        s.on_tick(m, 10_000, book)
        self.assertEqual(set(s.tried), {"HELD"})
        self.assertIsInstance(s.decisions, deque)
        self.assertEqual(s.decisions.maxlen, 1000)

    def test_scalp_b_cooldown_non_sol_pool_rx_pruned(self):
        s = Cupsey()
        s.cooldown.update({"GONE": 0, "HELD": 0})
        s.non_sol.update({"GONE", "HELD"})
        s.pool_rx.update({"GONE": 0, "HELD": 0})
        m, book = Market(), book_for(s)
        hold(book, "HELD")
        s.on_tick(m, 10_000, book)
        for c in (s.cooldown, s.non_sol, s.pool_rx):
            self.assertEqual(set(c), {"HELD"})

    def test_baselines_decided_pruned(self):
        for cls in (BaseRandom, BaseHold60):
            s = cls()
            s.decided.update({"GONE", "HELD"})
            m, book = Market(), book_for(s)
            hold(book, "HELD")
            s.on_tick(m, 10_000, book)
            self.assertEqual(s.decided, {"HELD"}, cls.name)

    def test_swing_sets_pruned_but_live_coins_kept(self):
        for s, name in ((MrFrog(), "skipped"), (Smokez(), "last_check"), (FrankDegods(), "last_check")):
            c = getattr(s, name)
            for mint in ("GONE", "HELD", "SEEN"):
                c.add(mint) if isinstance(c, set) else c.__setitem__(mint, 0)
            m, book = Market(), book_for(s)
            m._token("SEEN", 0)                          # still in the market: keep
            hold(book, "HELD")
            s.on_tick(m, 10_000, book)
            self.assertEqual(set(c), {"HELD", "SEEN"}, s.name)

    def test_frank_last_check_written_only_past_the_venue_gate(self):
        s = FrankDegods()
        m = Market()
        rows, rq, rb = A.launch("P", n=3)
        st = None
        for rx, ev in rows:
            st = m.apply(ev, rx)                         # a pump-curve coin, not migrated
        s.on_trade(st, rows[-1][1], rows[-1][0], book_for(s))
        self.assertNotIn("P", s.last_check)


class ExitStateAtFillTest(unittest.TestCase):
    """2: a Sell the simulator dropped must not leave the position stuck."""

    def test_scalp_a_dropped_take_profit_times_out_then_stop_fires(self):
        s = Decu()
        s.tp1_frac = 0.5
        m, st, rq, rb, t = market_with_launch()
        book = book_for(s)
        hold(book, "M", opened=t)
        p0 = st.price
        s.pos["M"] = {"entry": p0, "peak": p0, "opened": t, "tp_done": False}
        k = rq * rb
        rq2 = int(rq * 1.3)
        st = m.apply(A.trade("M", "bull", "buy", 5, rq2, k // rq2), t + 1000)
        out = s._exits_for(st, t + 1000, book)
        self.assertEqual([x.reason for x in out], ["Decu: take profit"])
        self.assertFalse(s.pos["M"]["tp_done"])          # only a fill may set it
        rq3 = int(rq * 0.6)
        st = m.apply(A.trade("M", "whale", "sell", 10, rq3, k // rq3), t + 2000)
        self.assertEqual(s._exits_for(st, t + 2000, book), [])     # TP still in flight
        late = t + 1000 + 3 * LAT + 1
        out = s._exits_for(st, late, book)              # never filled: give up waiting
        self.assertEqual([x.reason for x in out], ["Decu: hard stop"])

    def test_scalp_a_stop_fires_after_take_profit_fills(self):
        s = Decu()
        s.tp1_frac = 0.5
        m, st, rq, rb, t = market_with_launch()
        book = book_for(s)
        hold(book, "M", opened=t)
        s.pos["M"] = {"entry": st.price, "peak": st.price, "opened": t, "tp_done": False}
        k = rq * rb
        rq2 = int(rq * 1.3)
        st = m.apply(A.trade("M", "bull", "buy", 5, rq2, k // rq2), t + 1000)
        s._exits_for(st, t + 1000, book)
        rq3 = int(rq * 0.6)
        st = m.apply(A.trade("M", "whale", "sell", 10, rq3, k // rq3), t + 1500)
        self.assertEqual(s._exits_for(st, t + 1500, book), [])
        s.on_fill(fill("sell", "M", reason="Decu: take profit", t=t + 1000), book)
        self.assertTrue(s.pos["M"]["tp_done"])
        out = s._exits_for(st, t + 2001, book)
        self.assertEqual([x.reason for x in out], ["Decu: hard stop"])

    def test_scalp_b_tranche_done_only_at_fill(self):
        s = Cupsey()
        m, st, rq, rb, t = market_with_launch()
        book = book_for(s)
        hold(book, "M", opened=t)
        s.trips["M"] = Trip(t, st.price, st.price)
        k = rq * rb
        rq2 = int(rq * 1.4)
        st = m.apply(A.trade("M", "bull", "buy", 5, rq2, k // rq2), t + 1000)
        self.assertEqual([x.reason for x in s._exits(st, t + 1000, book)], ["take"])
        self.assertFalse(s.trips["M"].tranche_done)
        self.assertEqual([x.reason for x in s._exits(st, t + 1200, book)], ["take"])   # dropped: re-fire
        s.on_fill(fill("sell", "M", reason="take", t=t + 1000), book)
        self.assertTrue(s.trips["M"].tranche_done)
        self.assertNotIn("take", [x.reason for x in s._exits(st, t + 1500, book)])

    def test_tracked_stage_only_at_fill(self):
        s = Smokez()
        book = book_for(s)
        hold(book, "M", opened=0)
        s.pos["M"] = {"entry": 1.0, "opened": 0, "peak": 1.0, "stage": 0}
        out = s.exit_for("M", 1.6, 1000)
        self.assertTrue(out and out.reason.startswith("take-profit"))
        self.assertEqual(s.pos["M"]["stage"], 0)
        out = s.exit_for("M", 1.6, 1200)                # dropped by the sim: fires again
        self.assertTrue(out and out.reason.startswith("take-profit"))
        s.on_fill(fill("sell", "M", reason="take-profit +60%", t=1000), book)
        self.assertEqual(s.pos["M"]["stage"], 1)
        out = s.exit_for("M", 1.6, 1500)
        self.assertFalse(out and out.reason.startswith("take-profit"))


class CheapGatesFirstTest(unittest.TestCase):
    """3: holder statistics are not computed when a cheaper gate already fails."""

    def quiet_state(self, m, mint, venue="pump", rq=A.VSOL, rb=A.VTOK, created=0):
        st = m._token(mint, created * 1000)
        st.venue, st.seen_create, st.created_ts = venue, True, created
        st.price, st.reserve_quote, st.reserve_base, st.fee_bps = (rq / 1e9) / (rb / 1e6), rq, rb, 100
        st.holder_count = boom
        st.top_holder_share = boom
        return st

    def test_scalp_a_fresh_ok(self):
        s = Decu()
        st = self.quiet_state(Market(), "Q")
        self.assertFalse(s._fresh_ok(st, 10_000))        # age 10 s, no flow: no holder maths

    def test_smokez_wants(self):
        s = Smokez()
        rq = int(150e9)
        st = self.quiet_state(Market(), "Q", rq=rq, rb=int(A.VSOL * A.VTOK / rq))
        self.assertFalse(s.wants(st, 60_000))

    def test_scalp_b_entry(self):
        s = Cap()
        rq = B.CSOL
        st = self.quiet_state(Market(), "Q", rq=rq, rb=B.CTOK)
        st.progress = 0.6
        ev = A.trade("Q", "u", "sell", 0.1, rq, B.CTOK)
        self.assertEqual(s._entry(st, ev, 10_000, book_for(s)), [])


class TargetWalletTest(unittest.TestCase):
    """4: the target's own trade is never the trigger; an empty wallet does not skip empty users."""

    def test_wallets_declared(self):
        self.assertEqual(MrFrog.target_wallet, S.MRFROG)
        self.assertEqual(Smokez.target_wallet, S.SMOKEZ)
        self.assertEqual(FrankDegods.target_wallet, S.FRANK)

    def test_mr_frog_skips_target_trigger(self):
        rows, t = S.frog_launch(buyers=("a", "b", S.MRFROG))
        rows.append(S.trade(t + 1000, "d"))
        book, _ = S.run(rows, MrFrog())
        buys = S.fills(book, "buy")
        self.assertEqual([b.decision_ms for b in buys], [t + 1000])

    def test_smokez_skips_target_trigger(self):
        rows, t = S.smokez_run(users=("a", "b", "c", S.SMOKEZ))
        rows.append(S.trade(t + 2000, "e", rq=int(125e9)))
        book, _ = S.run(rows, Smokez())
        self.assertEqual([b.decision_ms for b in S.fills(book, "buy")], [t + 2000])

    def test_frank_skips_target_trigger(self):
        rows, t = S.frank_run()
        rx, ev = rows[60]
        rows[60] = (rx, ce.ChainEvent(**{**vars(ev), "user": S.FRANK}))
        rows.append(S.trade(t + 2000, "z", rq=int(3150e9), venue="pumpswap"))
        book, _ = S.run(rows, FrankDegods())
        self.assertEqual([b.decision_ms for b in S.fills(book, "buy")], [t + 2000])

    def test_empty_wallet_does_not_skip_empty_users(self):
        class Frog0(MrFrog):
            name, target_wallet = "frog0", ""
        rows, t = S.frog_launch(buyers=("a", "b", ""))
        book, _ = S.run(rows, Frog0())
        self.assertEqual([b.decision_ms for b in S.fills(book, "buy")], [t])

        class Cup0(Cupsey):
            name, target_wallet = "cup0", ""
        s = Cup0()
        m, st, rq, rb, t = market_with_launch()
        book = book_for(s)
        hold(book, "M", opened=t)
        s.trips["M"] = Trip(t, st.price * 2, st.price * 2)     # deep under water: stop is due
        ev = A.trade("M", "", "sell", 0.1, rq, rb)              # unknown wallet, not "the target"
        self.assertEqual([x.reason for x in s.on_trade(st, ev, t + 1000, book)], ["stop"])


class EliteCopyTest(unittest.TestCase):
    """5/6: only the elite's own event matches; the leader is remembered from the fill."""

    def setup(self):
        m = Market()
        m.elite_names = {"E1": "Decu"}
        m.apply(S.create(1000)[1], 1000)
        ev_e = S.trade(5000, "E1", sol=2.0)[1]
        ev_b = S.trade(5000, "b")[1]
        st = m.apply(ev_e, 5000)
        m.apply(ev_b, 5000)
        s = BaseEliteCopy()
        book = book_for(s)
        book.market = m
        return s, st, ev_e, ev_b, book

    def test_non_elite_trade_at_same_ms_is_not_a_copy(self):
        s, st, ev_e, ev_b, book = self.setup()
        self.assertEqual(s.on_trade(st, ev_b, 5000, book), [])
        out = s.on_trade(st, ev_e, 5000, book)
        self.assertEqual([type(x) for x in out], [Buy])

    def test_leader_set_at_fill_not_submit(self):
        s, st, ev_e, ev_b, book = self.setup()
        s.on_trade(st, ev_e, 5000, book)
        self.assertNotIn("M", s.leader)
        s.on_fill(fill("buy", "M", status="rejected", reason="copy Decu", t=5000), book)
        self.assertNotIn("M", s.leader)
        hold(book, "M")
        s.on_fill(fill("buy", "M", reason="copy Decu", t=5000), book)
        self.assertEqual(s.leader.get("M"), "Decu")


class DayRollTest(unittest.TestCase):
    """7: the kill switch measures from the day start, not from the first candidate."""

    def test_scalp_a_loss_before_first_candidate_counts(self):
        s = A.rec(Decu, daily_kill_dd=0.03, min_entry_gap_s=0.0)
        rows, rq, rb = A.launch("K1", n=16, rx0=DAY - 10_000)
        k = rq * rb
        rq2 = int(rq * 0.5)
        rows.append((DAY + 2_000, A.trade("K1", "whale", "sell", 10, rq2, k // rq2)))
        rows.append((DAY + 7_000, A.trade("K1", "late", "buy", 0.001, rq2, k // rq2)))
        r2, rq, rb = A.launch("K2", n=16, rx0=DAY + 60_000)
        rows += r2
        rows.append((DAY + 90_000, A.trade("K2", "late", "buy", 0.001, rq, rb)))
        r3, rq, rb = A.launch("K3", n=16, rx0=2 * DAY + 60_000)
        rows += r3
        rows.append((2 * DAY + 90_000, A.trade("K3", "late", "buy", 0.001, rq, rb)))
        A.run(rows, s)
        buys = [f.mint for f, _, _ in s.seen if f.side == "buy" and f.status == "filled"]
        self.assertEqual(buys, ["K1", "K3"])

    def test_tracked_rolls_day_on_tick(self):
        class R(Tracked):
            daily_kill_dd = 0.10
        r = R()
        b = SimpleNamespace(cash_sol=1.0, start_sol=1.0, positions={}, pending=[])
        b.pending_buy_sol = lambda: 0.0
        b.equity_sol = lambda m: b.cash_sol
        r.on_tick(Market(), DAY + 1000, b)
        b.cash_sol = 0.85                                 # lost 15 % before the first candidate
        self.assertFalse(r.may_enter(b, DAY + 2000))


class ZeroEntryTest(unittest.TestCase):
    """8: a zero entry price never raises inside the exit maths."""

    def test_scalp_a(self):
        s = Decu()
        m, st, rq, rb, t = market_with_launch()
        book = book_for(s)
        hold(book, "M", opened=t)
        s.pos["M"] = {"entry": 0.0, "peak": 0.0, "opened": t, "tp_done": False}
        self.assertIsInstance(s._exits_for(st, t + 1000, book), list)

    def test_scalp_b(self):
        s = Cupsey()
        m, st, rq, rb, t = market_with_launch()
        book = book_for(s)
        hold(book, "M", opened=t)
        s.trips["M"] = Trip(t, 0.0, 0.0)
        self.assertIsInstance(s._exits(st, t + 1000, book), list)


if __name__ == "__main__":
    unittest.main()
