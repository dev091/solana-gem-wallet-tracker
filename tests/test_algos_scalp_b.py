"""scalp_b reconstructions (Cupsey, Cooker, Trenchman, Cap): synthetic events through replay().

Checks: entry fires only when the filter holds, exits fire (stop / take / time), decisions are
suffix-invariant (no look-ahead), cash never goes negative and risk caps hold, the target
wallet's own trades never trigger an entry, non-SOL quotes are skipped, the liquidity cap
bounds price impact, and the daily kill switch stops new entries for the UTC day.
"""
import unittest

from gemtracker import chain_events as ce
from gemtracker.algos._scalp_b_base import liquidity_cap
from gemtracker.algos.cap import Cap
from gemtracker.algos.cooker import Cooker
from gemtracker.algos.cupsey import Cupsey
from gemtracker.algos.trenchman import Trenchman
from gemtracker.papersim import SimConfig, buy_out
from gemtracker.replay import replay
from gemtracker.tape import event_row

VSOL, VTOK = 40 * 10 ** 9, 800_000_000 * 10 ** 6          # price 5e-8 SOL -> mcap 50 SOL
CSOL, CTOK = 100 * 10 ** 9, 500_000_000 * 10 ** 6         # price 2e-7 SOL -> mcap 200 SOL
DAY = 86_400_000


def trade(mint, side, sol, rq, rb, user, rx, venue="pump", progress=0.3, quote_mint=ce.WSOL):
    return ce.ChainEvent("trade", venue, f"s{rx}{user}", 0, ts=rx // 1000, mint=mint, user=user,
                         side=side, quote=int(sol * 1e9), tokens=10 ** 6,
                         price=(rq / 1e9) / (rb / 1e6), reserve_quote=rq, reserve_base=rb,
                         fee_bps=100, progress=progress, quote_mint=quote_mint)


def launch(mint, n, sol_each=0.3, start=2_000, step=400, rq0=VSOL, rb0=VTOK, growth=0.15,
           progress=0.3, venue="pump", create=True, users=None, quote_mint=ce.WSOL, age0=1):
    """A create `age0` s before `start`, then n buys from distinct users with the price rising `growth`."""
    rows = []
    if create:
        c = start - age0 * 1000
        rows.append((c, ce.ChainEvent("create", "pump", "c" + mint, 0, ts=c // 1000, mint=mint, user="d",
                                          price=(rq0 / 1e9) / (rb0 / 1e6), reserve_quote=rq0,
                                          reserve_base=rb0, extra={"creator": "d"})))
    for i in range(n):
        f = 1 + growth * (i + 1) / n
        rq, rb = int(rq0 * f), int(rb0 / f)
        user = users[i] if users else f"u{i}{mint}"
        rows.append((start + i * step, trade(mint, "buy", sol_each, rq, rb, user, start + i * step,
                                             venue=venue, progress=progress, quote_mint=quote_mint)))
    return rows


def last_reserves(rows):
    ev = rows[-1][1]
    return ev.reserve_quote, ev.reserve_base


def flat(mint, rows, secs, every=2_000, start_after=3_000):
    """Buys from new users at a flat price for `secs` seconds after the scenario (keeps the clock going)."""
    rq, rb = last_reserves(rows)
    t0 = rows[-1][0] + start_after
    return [(t, trade(mint, "buy", 0.01, rq, rb, f"f{t}", t)) for t in range(t0, t0 + int(secs * 1000), every)]


def dump(mint, rows, drop=0.30, after=3_000):
    rq, rb = last_reserves(rows)
    f = (1 - drop) ** 0.5
    t = rows[-1][0] + after
    return [(t, trade(mint, "sell", 5.0, int(rq * f), int(rb / f), "whale", t))]


def pump(mint, rows, gain=0.40, after=3_000):
    rq, rb = last_reserves(rows)
    f = (1 + gain) ** 0.5
    t = rows[-1][0] + after
    return [(t, trade(mint, "buy", 5.0, int(rq * f), int(rb / f), "bull", t))]


def hot(cls, mint="M", **over):
    """A launch that satisfies `cls`'s entry filter."""
    spec = {
        Cupsey: dict(n=4),
        Cooker: dict(n=5),
        Trenchman: dict(n=16, age0=15, sol_each=0.2),
        Cap: dict(n=32, sol_each=0.15, rq0=CSOL, rb0=CTOK, progress=0.6),
    }[cls]
    spec.update(over)
    return launch(mint, **spec)


def recorder(cls):
    class Rec(cls):
        def __init__(self):
            super().__init__()
            self.seen = []

        def on_fill(self, fill, book):
            self.seen.append(fill)
            super().on_fill(fill, book)
    return Rec()


def run(rows_events, strat, latency=1000, start_usd=100.0):
    rows = [dict(event_row(ev, rx)) for rx, ev in sorted(rows_events, key=lambda r: r[0])]
    sim, market = replay([strat], SimConfig(latency_ms=latency, venue_latency_ms={}, start_usd=start_usd),
                         rows, 116.0)
    book = sim.books[strat.name]
    assert getattr(book, "errors", 0) == 0, "strategy raised inside the sim"
    return sim, market, book


def fills(strat, side=None, status="filled"):
    return [f for f in strat.seen if (side is None or f.side == side) and f.status == status]


ALGOS = (Cupsey, Cooker, Trenchman, Cap)


class EntryTest(unittest.TestCase):
    def test_entry_fires_on_hot_launch(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                run(hot(cls), s)
                buys = fills(s, "buy")
                self.assertEqual(len(buys), 1)
                self.assertEqual(buys[0].mint, "M")

    def test_no_entry_when_filter_fails(self):
        cases = {
            Cupsey: hot(Cupsey, users=["a", "a", "a", "a"]),                      # one buyer
            Cooker: hot(Cooker, start=40_000, age0=39),                            # 39 s old
            Trenchman: hot(Trenchman, n=5),                                        # few holders
            Cap: hot(Cap, progress=0.3),                                           # not late curve
        }
        for cls, rows in cases.items():
            with self.subTest(cls.name):
                s = recorder(cls)
                run(rows, s)
                self.assertEqual(fills(s, "buy"), [])

    def test_cooker_skips_coins_where_dev_sold(self):
        rows = hot(Cooker)
        rq, rb = rows[1][1].reserve_quote, rows[1][1].reserve_base
        rows.insert(1, (1_200, trade("M", "buy", 0.5, rq, rb, "d", 1_200)))
        rows.insert(2, (1_400, trade("M", "sell", 0.2, rq, rb, "d", 1_400)))
        s = recorder(Cooker)
        run(rows, s)
        self.assertEqual(fills(s, "buy"), [])

    def test_never_triggers_on_target_wallet(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                rows = hot(cls)
                s = recorder(cls)
                run(rows, s)
                at = fills(s, "buy")[0].decision_ms
                k = next(i for i, (rx, ev) in enumerate(rows) if rx == at)
                upto = rows[:k + 1]                      # nothing after the triggering trade
                s = recorder(cls)
                run(upto, s)
                self.assertEqual(len(fills(s, "buy")), 1)
                ev = upto[k][1]
                mine = trade(ev.mint, ev.side, ev.quote / 1e9, ev.reserve_quote, ev.reserve_base,
                             cls.target_wallet, at, venue=ev.venue, progress=ev.progress)
                s = recorder(cls)
                run(upto[:k] + [(at, mine)], s)          # same trade, but it is the target's own
                self.assertEqual(fills(s, "buy"), [], cls.name)

    def test_non_sol_quote_is_skipped(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                run(hot(cls, quote_mint="XspzcW1111111111111111111111111111111111111"), s)
                self.assertEqual(fills(s, "buy"), [])


class ExitTest(unittest.TestCase):
    def test_hard_stop_exits_after_dump(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                rows = hot(cls)
                rows += dump("M", rows, drop=0.35)
                _, _, book = run(rows, s)
                sells = fills(s, "sell")
                self.assertEqual([f.reason for f in sells], ["stop"])
                self.assertNotIn("M", book.positions)

    def test_time_stop_exits_flat_coin(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                rows = hot(cls)
                rows += flat("M", rows, cls.time_stop_s + 10)
                _, _, book = run(rows, s)
                sells = fills(s, "sell")
                self.assertEqual([f.reason for f in sells], ["time"])
                held = sells[0].decision_ms - fills(s, "buy")[0].arrival_ms
                self.assertGreaterEqual(held, cls.time_stop_s * 1000)
                self.assertLess(held, cls.time_stop_s * 1000 + 3_000)

    def test_take_profit_fires(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                rows = hot(cls)
                rows += pump("M", rows, gain=cls.take_profit + 0.15)
                rows += flat("M", rows, 4)
                _, _, book = run(rows, s)
                sells = fills(s, "sell")
                self.assertTrue(sells and sells[0].reason == "take", [f.reason for f in sells])
                if cls.take_profit_frac < 1:
                    self.assertIn("M", book.positions)
                else:
                    self.assertNotIn("M", book.positions)


class DisciplineTest(unittest.TestCase):
    def test_decisions_are_suffix_invariant(self):
        """What the algo decided by time T does not depend on rows after T."""
        for cls in ALGOS:
            with self.subTest(cls.name):
                full_rows = hot(cls)
                cut = full_rows[-1][0]
                full_rows = full_rows + dump("M", full_rows) + hot(cls, "N", start=cut + 60_000)
                a, b = recorder(cls), recorder(cls)
                run(full_rows, a)
                run([r for r in full_rows if r[0] <= cut], b)
                key = lambda f: (f.side, f.mint, f.decision_ms, round(f.sol, 9), f.status)
                early = [key(f) for f in a.seen if f.decision_ms <= cut]
                self.assertEqual(early, [key(f) for f in b.seen])
                self.assertTrue(early)

    def test_never_exceeds_cash_and_respects_caps(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                rows = []
                for i in range(6):
                    rows += hot(cls, f"M{i}", start=16_000 + i * 3_000)
                _, market, book = run(rows, s)
                buys = fills(s, "buy")
                self.assertEqual(len(buys), cls.max_positions)
                self.assertGreaterEqual(book.cash_sol, 0)
                spent = sum(f.sol + f.tx_fee_sol for f in buys)
                self.assertLessEqual(spent, book.start_sol)
                self.assertLessEqual(spent, cls.max_exposure_frac * book.start_sol * 1.02)
                for f in buys:
                    self.assertLessEqual(f.sol, cls.size_frac * book.start_sol * 1.001)

    def test_entry_is_a_fraction_of_equity_not_fixed(self):
        s1, s2 = recorder(Cupsey), recorder(Cupsey)
        big = dict(rq0=4_000 * 10 ** 9, rb0=80_000_000_000 * 10 ** 6)   # deep pool, same price
        run(hot(Cupsey, **big), s1, start_usd=100.0)
        run(hot(Cupsey, **big), s2, start_usd=1_000.0)
        a, b = fills(s1, "buy")[0].sol, fills(s2, "buy")[0].sol
        self.assertAlmostEqual(b / a, 10.0, places=2)
        self.assertAlmostEqual(a, Cupsey.size_frac * 100 / 116, places=3)

    def test_liquidity_cap_bounds_price_impact(self):
        st = type("S", (), {"reserve_quote": VSOL, "reserve_base": VTOK, "fee_bps": 100})()
        sol = liquidity_cap(st, 0.05)
        tokens, fee = buy_out(sol, 100, VSOL, VTOK)
        after = (VSOL + (sol - fee) * 1e9) / (VTOK - tokens * 1e6)
        impact = after / (VSOL / VTOK) - 1
        self.assertLessEqual(impact, 0.0501)
        self.assertGreater(impact, 0.045)
        # a rich book on a thin pool is capped at that spend
        s = recorder(Cupsey)
        rows = hot(Cupsey)
        run(rows, s, start_usd=1_000_000.0)
        f = fills(s, "buy")[0]
        ev = next(ev for rx, ev in rows if rx == f.decision_ms)
        st.reserve_quote, st.reserve_base = ev.reserve_quote, ev.reserve_base
        self.assertLessEqual(f.sol, liquidity_cap(st, 0.05) * 1.001)
        self.assertLess(f.sol, 2.0)                      # not the 1 500 SOL the fraction would allow

    def test_daily_kill_switch_blocks_new_entries_until_next_utc_day(self):
        s = recorder(Cupsey)
        s.daily_kill_dd = 0.02
        rows = hot(Cupsey, "A")
        rows += dump("A", rows, drop=0.35)
        rows += hot(Cupsey, "B", start=rows[-1][0] + 20_000)          # same day: blocked
        rows += hot(Cupsey, "C", start=rows[-1][0] + DAY)              # next day: allowed
        run(rows, s)
        self.assertEqual([f.mint for f in fills(s, "buy")], ["A", "C"])
        self.assertEqual([f.reason for f in fills(s, "sell")], ["stop"])

    def test_names_are_unique_and_params_are_class_attributes(self):
        names = {c.name for c in ALGOS}
        self.assertEqual(len(names), 4)
        for cls in ALGOS:
            for attr in ("size_frac", "max_impact", "max_exposure_frac", "max_positions",
                         "max_loss_per_trade", "daily_kill_dd", "time_stop_s", "target_wallet"):
                self.assertIn(attr, dir(cls))
            self.assertTrue(cls.target_wallet)


if __name__ == "__main__":
    unittest.main()
