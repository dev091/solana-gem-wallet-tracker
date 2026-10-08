"""The five autonomous elite-style algos (gemtracker/algos/elite5.py) and the scalp_b ET kill switch."""
import unittest
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from test_algos_scalp_b import VSOL, VTOK, dump, flat, fills, launch, recorder, run, trade
from gemtracker.algos.cupsey import Cupsey
from gemtracker.algos.elite5 import CentedHold, CookerOld, FrogDip, TheoHold, TrunoestHold

ALGOS = (FrogDip, CookerOld, TrunoestHold, TheoHold, CentedHold)


def frog_scene(mint="F", seller="s1"):
    """A coin pumped to ~72 SOL mcap, quiet for 100 s, then one sell drops it to ~45 SOL."""
    rows = launch(mint, n=5, sol_each=0.3, growth=0.2, age0=200)
    rows += [(rx + 100_000, ev) for rx, ev in dump(mint, rows, drop=0.38, after=0)]
    rows[-1] = (rows[-1][0], trade(mint, "sell", 5.0, rows[-1][1].reserve_quote, rows[-1][1].reserve_base,
                                   seller, rows[-1][0]))
    return rows + flat(mint, rows, 20, every=5_000)


SCENES = {
    FrogDip: frog_scene,
    CookerOld: lambda m="M": launch(m, n=8, sol_each=0.2, growth=0.10, age0=200, step=500),
    TrunoestHold: lambda m="M": launch(m, n=16, sol_each=0.2, growth=0.30, age0=40, step=500),
    TheoHold: lambda m="M": launch(m, n=10, sol_each=0.2, growth=0.09, age0=40, step=500),
    CentedHold: lambda m="M": launch(m, n=12, sol_each=0.2, growth=0.20, age0=40, step=500),
}


class Elite5(unittest.TestCase):
    def test_each_algo_enters_on_its_own_scene(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                rows = SCENES[cls]()
                run(rows + flat("M" if cls is not FrogDip else "F", rows, 10), s)
                self.assertEqual(len(fills(s, "buy")), 1)

    def test_launch_snipes_are_never_taken(self):
        for cls in ALGOS:
            with self.subTest(cls.name):
                s = recorder(cls)
                rows = launch("L", n=16, sol_each=0.3, growth=0.3, age0=1, step=300)
                run(rows + flat("L", rows, 10), s)
                self.assertEqual(fills(s, "buy"), [])

    def test_frog_never_triggers_on_mr_frog_own_sell(self):
        s = recorder(FrogDip)
        run(frog_scene(seller=FrogDip.target_wallet), s)
        self.assertEqual(fills(s, "buy"), [])

    def test_frog_skips_coin_at_its_high(self):
        s = recorder(FrogDip)
        rows = launch("F", n=5, sol_each=0.3, growth=0.2, age0=200)
        rq, rb = rows[-1][1].reserve_quote, rows[-1][1].reserve_base
        t = rows[-1][0] + 100_000
        rows.append((t, trade("F", "sell", 0.01, rq, rb, "s1", t)))     # sell with no price drop
        run(rows + flat("F", rows, 20, every=5_000), s)
        self.assertEqual(fills(s, "buy"), [])

    def test_names_unique_and_wallets_only_as_non_triggers(self):
        self.assertEqual(len({c.name for c in ALGOS}), 5)
        for cls in ALGOS:
            self.assertTrue(cls.target_wallet)
            self.assertEqual(cls.size_frac, 0.20)
            self.assertGreater(cls.min_age_s, 1.0)          # no launch sniping


class ScalpBKillSwitchET(unittest.TestCase):
    def test_kill_switch_day_is_the_et_day_not_utc(self):
        et = ZoneInfo("America/New_York")
        ms = lambda *a: int(datetime(*a, tzinfo=et).timestamp() * 1000)
        s = Cupsey()
        book = SimpleNamespace(cash_sol=1.0, positions={})
        s._roll_day(ms(2026, 10, 7, 19, 0), book)            # 23:00 UTC
        book.cash_sol = 0.8
        s._roll_day(ms(2026, 10, 7, 20, 30), book)           # 00:30 UTC next day, same ET day
        self.assertTrue(s.killed)
        s._roll_day(ms(2026, 10, 8, 0, 5), book)             # new ET day
        self.assertFalse(s.killed)


if __name__ == "__main__":
    unittest.main()
