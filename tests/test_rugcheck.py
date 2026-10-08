"""Rug filter every algo runs before a buy (gemtracker/rugcheck.py): same checks for all, fail closed."""
import itertools
import unittest

from gemtracker import rugcheck as R
from gemtracker.chain_events import ChainEvent, PUMP_SUPPLY
from gemtracker.market import Market

T0 = 1_790_000_000          # chain seconds
DEV, MINT = "Dev", "Mint1pump"
PCT = PUMP_SUPPLY / 100     # 1% of supply, whole tokens
_sig = itertools.count()


def ev(kind, user="", side="", tokens=0.0, ts=T0, venue="pump", extra=None, rq=40e9):
    return ChainEvent(kind=kind, venue=venue, signature=f"s{next(_sig)}", index=0, ts=ts, mint=MINT, user=user,
                      side=side, quote=int(tokens * 3e-8 * 1e9), tokens=int(tokens * 1e6), price=3e-8,
                      reserve_quote=int(rq), reserve_base=int(800e6 * 1e6), extra=extra or {})


class Scene:
    """A fair pump coin: dev holds 2%, thirty wallets 0.5% each, all bought after the snipe window."""

    def __init__(self, create=True, venue="pump", creator=DEV):
        self.m = Market()
        if create:
            self.do(ev("create", creator, venue=venue, extra={"creator": creator} if creator else {}))
            if creator:
                self.buy(creator, 2, T0)
        for i in range(30):
            self.buy(f"w{i}", 0.5, T0 + 10 + i, venue=venue)

    def do(self, e):
        self.st = self.m.apply(e, e.ts * 1000)

    def buy(self, user, pct, ts, venue="pump"):
        self.do(ev("trade", user, "buy", pct * PCT, ts, venue))

    def sell(self, user, pct, ts):
        self.do(ev("trade", user, "sell", pct * PCT, ts))

    def check(self, at=T0 + 60, size_sol=0.1, meta=None):
        return R.check(self.st, at * 1000, size_sol, meta=meta)


GOOD_EXT = R.Meta(top10_share=0.12, mint_authority=False, freeze_authority=False, bad_extensions=(),
                  lp_locked=1.0, liquidity_usd=250_000.0, sell_impact=0.01)


class RugCheck(unittest.TestCase):
    def test_a_fair_coin_passes(self):
        v = Scene().check()
        self.assertTrue(v.ok, v.reasons)
        self.assertEqual(v.reasons, ())

    def test_no_sniping_a_young_coin(self):
        self.assertIn("young", Scene().check(at=T0 + 20).reasons)

    def test_pool_must_be_deep_versus_our_size(self):
        s = Scene()
        self.assertTrue(s.check(size_sol=1.9).ok)          # 40 SOL reserve >= 20 x 1.9
        self.assertEqual(s.check(size_sol=3).reasons, ("thin",))

    def test_top10_concentration(self):
        s = Scene()
        s.buy("whale", 25, T0 + 45)
        self.assertEqual(s.check().reasons, ("concentrated",))

    def test_dev_still_holding_a_big_bag(self):
        s = Scene()
        s.buy(DEV, 4, T0 + 45)
        self.assertEqual(s.check().reasons, ("dev_heavy",))

    def test_bundled_launch_and_sold_out_snipers_stop_counting(self):
        s = Scene()
        for i in range(5):
            s.buy(f"b{i}", 5, T0 + 1)                         # 25% inside the 2 s window
        self.assertEqual(s.check().reasons, ("bundled",))
        for i in range(2):
            s.sell(f"b{i}", 5, T0 + 50)                       # 15% left
        self.assertTrue(s.check().ok, s.check().reasons)

    def test_buyers_seen_before_the_create_count_as_snipers(self):
        s = Scene(create=False)
        s.m = Market()
        s.buy("early", 25, T0)
        s.do(ev("create", DEV, extra={"creator": DEV}))
        self.assertIn("bundled", s.check().reasons)
        self.assertNotIn(DEV, s.st.snipers)

    def test_dev_selling_blocks_buys_for_two_minutes(self):
        s = Scene()
        s.sell(DEV, 1, T0 + 50)
        self.assertEqual(s.check().reasons, ("dev_dumping",))
        self.assertTrue(s.check(at=T0 + 171).ok)

    def test_unknown_creator_never_matches_anonymous_trades(self):
        s = Scene(creator="")
        s.do(ev("trade", "", "sell", PCT, T0 + 55))
        self.assertTrue(s.check().ok, s.check().reasons)

    def test_partial_history_needs_outside_holder_data(self):
        s = Scene(create=False, venue="pumpswap")
        fair = dict(top10_share=0.12, dev_share=0.01, sniper_share=0.05)
        at = T0 + 100
        self.assertEqual(s.check(at=at).reasons, ("partial_history",))
        for missing in fair:                                  # a pump coin needs all three
            meta = R.Meta(**{k: v for k, v in fair.items() if k != missing})
            self.assertEqual(s.check(at=at, meta=meta).reasons, ("partial_history",), missing)
        self.assertTrue(s.check(at=at, meta=R.Meta(**fair)).ok)
        for change, reason in [(dict(top10_share=0.4), "concentrated"), (dict(dev_share=0.08), "dev_heavy"),
                               (dict(sniper_share=0.3), "bundled"),
                               (dict(dev_last_sell_ms=(at - 60) * 1000), "dev_dumping")]:
            self.assertEqual(s.check(at=at, meta=R.Meta(**{**fair, **change})).reasons, (reason,), change)
        self.assertTrue(s.check(at=at, meta=R.Meta(**fair, dev_last_sell_ms=(at - 121) * 1000)).ok)

    def test_other_dexes_must_prove_every_safety_fact(self):
        s = Scene(create=False, venue="jup")
        self.assertTrue(s.check(at=T0 + 100, meta=GOOD_EXT).ok)
        self.assertEqual(set(s.check(at=T0 + 100).reasons),
                         {"partial_history", "mint_authority", "freeze_authority", "token2022", "lp_unlocked",
                          "unsellable", "thin"})
        bad = [(dict(mint_authority=True), "mint_authority"), (dict(freeze_authority=True), "freeze_authority"),
               (dict(bad_extensions=("transfer_hook",)), "token2022"), (dict(lp_locked=0.5), "lp_unlocked"),
               (dict(sell_impact=0.2), "unsellable"), (dict(liquidity_usd=20_000.0), "thin")]
        for change, reason in bad:
            meta = R.Meta(**{**GOOD_EXT.__dict__, **change})
            self.assertEqual(s.check(at=T0 + 100, meta=meta).reasons, (reason,), change)

    def test_tail_aware_size(self):
        self.assertAlmostEqual(R.risk_size_frac(0.9), 0.05 / 0.9)    # one rug costs at most 5%
        self.assertEqual(R.risk_size_frac(0.1), 0.25)                 # hard cap
        self.assertEqual(R.risk_size_frac(0.5, kelly=0.04), 0.04)     # Kelly smaller: Kelly wins
        self.assertEqual(R.risk_size_frac(0.5, kelly=-0.1), 0.0)      # no edge: no bet
        for bad in (0, -0.2, 1.5):
            with self.assertRaises(ValueError):
                R.risk_size_frac(bad)


if __name__ == "__main__":
    unittest.main()
