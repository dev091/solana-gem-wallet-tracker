import time
import unittest

from gemtracker.config import IGNORED_MINTS, STABLES, Criteria
from gemtracker.criteria import GEM_HUNTER, REJECTED, STRICT, WalletReport, evaluate
from gemtracker.prices import TokenQuote
from gemtracker.solana import TxDelta
from gemtracker.trades import Position, apply_quotes, build_positions, trade_events
from tests.helpers import addr

SOL_USD = 200.0
USDC = next(m for m, s in STABLES.items() if s == "USDC")
JITOSOL = next(m for m, s in IGNORED_MINTS.items() if s == "JitoSOL")
DAY = 86400
NOW = 1_760_000_000


def price(_ts):
    return SOL_USD


def d(sig, ts, sol, **tokens):
    return TxDelta(sig, ts, ts, sol, tokens)


class TradeEventsTest(unittest.TestCase):
    def test_buy_sell_transfer_classification(self):
        m = addr("m")
        self.assertEqual([(e.kind, e.usd) for e in trade_events(d("b", 1, -1.5, **{m: 1000}), price)],
                         [("buy", 300.0)])
        self.assertEqual([(e.kind, e.usd) for e in trade_events(d("s", 2, 600, **{m: -1000}), price)],
                         [("sell", 120_000.0)])
        # Only the network fee left the wallet: tokens were sent/received, not traded.
        self.assertEqual([e.kind for e in trade_events(d("t", 3, -0.000005, **{m: 50}), price)], ["transfer_in"])
        self.assertEqual([e.kind for e in trade_events(d("o", 4, -0.000005, **{m: -50}), price)], ["transfer_out"])

    def test_stablecoin_trades_and_ignored_moves(self):
        m = addr("m")
        self.assertEqual([(e.kind, e.usd) for e in trade_events(d("u", 1, 0, **{USDC: -250.0, m: 9}), price)],
                         [("buy", 250.0)])
        self.assertEqual(trade_events(d("q", 1, -1.0, **{USDC: 200.0}), price), [])   # SOL -> USDC
        self.assertEqual(trade_events(d("l", 1, -10.0, **{JITOSOL: 9.0}), price), [])  # staking
        self.assertEqual(trade_events(d("n", 1, -0.01), price), [])                    # plain SOL move

    def test_token_for_token_swap_is_not_counted_as_a_buy(self):
        a, b = addr("a"), addr("b")
        kinds = sorted(e.kind for e in trade_events(d("x", 1, -0.000005, **{a: -5, b: 7}), price))
        self.assertEqual(kinds, ["transfer_in", "transfer_out"])


class PositionsTest(unittest.TestCase):
    def test_history_replay(self):
        m = addr("gem")
        positions = build_positions([
            d("sell", 20, 600.0, **{m: -1000}),   # out of order on purpose
            d("buy", 10, -1.5, **{m: 1000}),
        ], price)
        (p,) = positions
        self.assertEqual((p.cost_usd, p.proceeds_usd, p.buys, p.sells), (300.0, 120_000.0, 1, 1))
        self.assertEqual((p.first_buy_ts, p.first_buy_sig), (10, "buy"))
        self.assertAlmostEqual(p.multiple, 400.0)
        self.assertAlmostEqual(p.realized_usd, 119_700.0)
        self.assertAlmostEqual(p.balance, 0.0)

    def test_quotes_value_holdings_conservatively(self):
        live, dead = addr("live"), addr("dead")
        positions = build_positions([d("1", 1, -1, **{live: 1000}), d("2", 1, -1, **{dead: 1000})], price)
        apply_quotes(positions, {live: TokenQuote(live, "LIVE", price=50.0, liquidity=40_000.0, launched_ts=0),
                                 dead: TokenQuote(dead, "DEAD", price=1.0, liquidity=10.0)})
        by = {p.mint: p for p in positions}
        self.assertEqual(by[live].value_usd, 20_000.0)  # 1000 x $50 = $50k, capped at half the pool
        self.assertEqual(by[live].symbol, "LIVE")
        self.assertEqual(by[dead].value_usd, 0.0)
        self.assertIn("no liquidity (dead / rugged)", by[dead].flags)


def pos(name, cost, out, held=0.0, age_days=30, **kw):
    p = Position(addr(name), symbol=name.upper(), cost_usd=cost, proceeds_usd=out, value_usd=held,
                 buys=1 if cost else 0, sells=1 if out else 0, first_buy_ts=NOW - age_days * DAY, **kw)
    p.bought = 1.0
    return p


def gems(n):
    return [pos(f"gem{i}", 200 + i * 50, 150_000 + i * 10_000) for i in range(n)]


class CriteriaTest(unittest.TestCase):
    def check(self, positions, crit=None, **kw):
        return evaluate(WalletReport(addr("w"), positions, **kw), crit or Criteria.preset("gems"), now=NOW)

    def test_perfect_gem_hunter_is_strict(self):
        v = self.check(gems(5))
        self.assertEqual(v.tier, STRICT, v.reasons)
        self.assertEqual(v.stats["gems"], 5)
        self.assertEqual(v.stats["losses"], 0)

    def test_one_scam_coin_breaks_the_strict_rule(self):
        v = self.check(gems(5) + [pos("rug", 300, 3)])
        self.assertEqual(v.tier, GEM_HUNTER)
        self.assertTrue(any("under 20x" in r for r in v.reasons))
        self.assertEqual(v.stats["losses"], 1)

    def test_every_trade_needs_20x_not_just_profit(self):
        v = self.check(gems(4) + [pos("ok", 300, 300 * 19)])
        self.assertEqual(v.tier, GEM_HUNTER)
        self.assertEqual(self.check(gems(4) + [pos("ok", 300, 300 * 20)]).tier, STRICT)

    def test_entry_size_rules(self):
        whale = pos("big", 2_000, 2_000 * 60)
        self.assertEqual(self.check(gems(4) + [whale]).tier, GEM_HUNTER)
        self.assertEqual(self.check(gems(4) + [whale], Criteria.preset("gems", all_entries_in_range=False)).tier, STRICT)
        # $600 in -> $200k out is a great trade but not a $100-$500 gem.
        self.assertEqual(self.check(gems(3) + [pos("x", 600, 200_000)], Criteria.preset("gems", all_entries_in_range=False)).stats["gems"], 3)

    def test_needs_minimum_number_of_gems(self):
        v = self.check(gems(3))
        self.assertEqual(v.tier, REJECTED)
        self.assertEqual(self.check(gems(4), Criteria.preset("gems", min_gems=5)).tier, REJECTED)

    def test_fresh_trades_are_not_judged_yet(self):
        v = self.check(gems(4) + [pos("new", 300, 0, held=310, age_days=1)])
        self.assertEqual(v.tier, STRICT)
        self.assertEqual(v.stats["open"], 1)

    def test_unrealized_only_counts_when_asked(self):
        paper = pos("paper", 300, 40_000, held=90_000)
        self.assertEqual(self.check(gems(3) + [paper]).tier, REJECTED)
        self.assertEqual(self.check(gems(3) + [paper], Criteria.preset("gems", count_unrealized=True)).tier, STRICT)

    def test_bots_and_incomplete_history_never_strict(self):
        self.assertEqual(self.check([], too_active=True, history_complete=False, tx_count=3000).tier, REJECTED)
        self.assertEqual(self.check(gems(5), history_complete=False).tier, GEM_HUNTER)
        self.assertEqual(self.check(gems(5), Criteria.preset("gems", max_tokens=3)).tier, GEM_HUNTER)

    def test_insider_flags(self):
        sniped = gems(4)
        for p in sniped[:2]:
            p.launched_ts = p.first_buy_ts - 3
        never_bought = pos("airdrop", 0, 50_000)
        v = self.check(sniped + [never_bought])
        self.assertEqual(v.tier, STRICT)
        self.assertTrue(any("within 60s of launch" in f for f in v.flags))
        self.assertTrue(any("never bought" in f for f in v.flags))


if __name__ == "__main__":
    unittest.main()


class QuotesTest(unittest.TestCase):
    def test_missing_liquidity_is_unknown_not_zero(self):
        from unittest import mock
        from gemtracker import net, prices
        curve, amm = addr("curve-coin"), addr("amm-coin")
        pairs = [
            {"baseToken": {"address": curve, "symbol": "NEW"}, "priceUsd": "0.00001", "pairCreatedAt": 1_700_000_000_000},
            {"baseToken": {"address": amm, "symbol": "OLD"}, "priceUsd": "0.5", "liquidity": {"usd": 900}},
            {"baseToken": {"address": amm, "symbol": "OLD"}, "priceUsd": "0.6", "liquidity": {"usd": 80_000},
             "pairCreatedAt": 1_600_000_000_000},
        ]
        with mock.patch.object(net, "get_json", return_value=pairs):
            q = prices.token_quotes([curve, amm])
        self.assertIsNone(q[curve].liquidity)
        self.assertEqual(q[curve].price, 0.00001)
        self.assertEqual((q[amm].price, q[amm].liquidity, q[amm].launched_ts), (0.6, 80_000, 1_600_000_000))
        positions = build_positions([d("b", 1, -1, **{curve: 1000})], price)
        apply_quotes(positions, q)
        self.assertAlmostEqual(positions[0].value_usd, 0.01)  # unknown liquidity: still valued


class SolanaPresetTest(unittest.TestCase):
    """Default rules: every trade 5x+, zero losses, verified coins only, at least 5 such trades."""

    def check(self, positions, **crit):
        return evaluate(WalletReport(addr("w"), positions), Criteria(**crit), now=NOW)

    def wins(self, n, mult=6.0, verified=True):
        out = [pos(f"w{i}", 1000, 1000 * mult) for i in range(n)]
        for p in out:
            p.verified = verified
        return out

    def test_five_verified_5x_trades_pass(self):
        v = self.check(self.wins(5))
        self.assertEqual(v.tier, STRICT, v.reasons)
        self.assertEqual(v.stats["gems"], 5)

    def test_one_loss_or_one_4x_fails(self):
        loss = pos("loss", 1000, 900)
        loss.verified = True
        v = self.check(self.wins(5) + [loss])
        self.assertEqual(v.tier, GEM_HUNTER)
        self.assertTrue(any("under 5x" in r for r in v.reasons))
        self.assertEqual(self.check(self.wins(4) + self.wins(1, mult=4.0)).tier, REJECTED)

    def test_unverified_coin_breaks_the_rule(self):
        v = self.check(self.wins(5) + self.wins(1, verified=False))
        self.assertTrue(any("not verified" in r for r in v.reasons))
        self.assertEqual(self.check(self.wins(5, verified=False)).tier, REJECTED)
        self.assertEqual(self.check(self.wins(5, verified=False), verified_only=False).tier, STRICT)
        self.assertEqual(self.check(self.wins(5, verified=None)).tier, STRICT)  # list unavailable: rule skipped

    def test_too_few_trades(self):
        self.assertEqual(self.check(self.wins(4)).tier, REJECTED)
        self.assertEqual(self.check(self.wins(4), min_trades=4).tier, STRICT)
