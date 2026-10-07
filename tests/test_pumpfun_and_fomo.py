import json
import pathlib
import tempfile
import unittest
from unittest import mock

from gemtracker import config, pumpfun, sources
from gemtracker.config import FOMO_SIGNER, STABLES, Criteria
from gemtracker.providers import RpcProvider
from gemtracker.solana import History, delta_from_rpc_tx
from gemtracker.sources import CandidateBook
from gemtracker.util import b58decode
from tests.helpers import SOL, addr, rpc_tx
from tests.test_solana import FakeRpc

USDC = next(m for m, s in STABLES.items() if s == "USDC")


class ProgramAddressTest(unittest.TestCase):
    def test_known_pump_fun_accounts(self):
        # Fixed accounts every Pump.fun transaction uses.
        for seed, expected in ((b"global", "4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf"),
                               (b"__event_authority", "Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1"),
                               (b"mint-authority", "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM")):
            self.assertEqual(pumpfun.find_program_address([seed], pumpfun.PUMP_PROGRAM)[0], expected)

    def test_curve_check(self):
        # Real wallets are ed25519 points; program addresses are not.
        for wallet in (FOMO_SIGNER, "J9WiAZKf8JnCkHFL8fLCCXdEgdoLjLRqU2EGsDjdqYga",
                       "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"):
            self.assertTrue(pumpfun._on_curve(b58decode(wallet)), wallet)
        self.assertFalse(pumpfun._on_curve(b58decode("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")))
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError:
            return
        for _ in range(50):
            key = Ed25519PrivateKey.generate().public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            self.assertTrue(pumpfun._on_curve(key))

    def test_b58_round_trip(self):
        for value in (addr("x"), "11111111111111111111111111111111", FOMO_SIGNER):
            self.assertEqual(pumpfun.b58encode(b58decode(value)), value)


class EarlyBuyersTest(unittest.TestCase):
    def test_reads_the_oldest_trades_and_keeps_in_range_entries(self):
        mint = addr("big-coin")
        curve = pumpfun.bonding_curve(mint)
        a, b, c, seller = addr("a"), addr("b"), addr("smart-wallet"), addr("seller")
        newest = [{"signature": f"n{i}", "err": None} for i in range(1000)]
        oldest = [{"signature": s, "err": None} for s in ("sell", "buy-b", "buy-a")] + \
                 [{"signature": "create", "err": {"x": 1}}]  # newest first, like the RPC
        txs = {
            "buy-a": rpc_tx(a, "buy-a", 100, sol_before=10 * SOL, sol_after=8_500_000_000,
                            post_tokens=[(mint, 10 ** 12, 6)]),
            "buy-b": rpc_tx(b, "buy-b", 101, sol_before=50 * SOL, sol_after=40 * SOL,
                            post_tokens=[(mint, 10 ** 13, 6)]),
            "sell": rpc_tx(seller, "sell", 102, sol_before=1 * SOL, sol_after=2 * SOL,
                           pre_tokens=[(mint, 10 ** 12, 6), (mint, 5 * 10 ** 13, 6, curve)],
                           post_tokens=[(mint, 0, 6), (mint, 5 * 10 ** 13 + 10 ** 12, 6, curve)]),
        }
        # A smart wallet (not a signer) buying with USDC through a relayer.
        txs["buy-c"] = rpc_tx(FOMO_SIGNER, "buy-c", 103,
                              pre_tokens=[(USDC, 400_000_000, 6, c)],
                              post_tokens=[(USDC, 100_000_000, 6, c), (mint, 10 ** 11, 6, c)])
        oldest.insert(0, {"signature": "buy-c", "err": None})
        rpc = FakeRpc([newest, oldest], txs)
        buyers, note = pumpfun.early_buyers(rpc, mint, lambda ts: 150.0, Criteria.preset("gems"), early_txs=10)
        found = {w: round(usd) for w, usd, _ in buyers}
        self.assertEqual(found, {a: 225, c: 300})  # b paid $1,500; the curve and the seller are not buyers
        rpc.sig_pages = [newest, oldest]
        wide, _ = pumpfun.early_buyers(rpc, mint, lambda ts: 150.0, Criteria(), early_txs=10)
        self.assertEqual({w for w, _, _ in wide}, {a, b, c})  # default rules: any buy of $20+
        self.assertIn("in range", note)
        first_call = rpc.calls[0]
        self.assertEqual(first_call[1][0], curve)

    def test_gives_up_when_launch_is_too_far_back(self):
        page = [{"signature": f"s{i}", "err": None} for i in range(1000)]
        rpc = FakeRpc([page] * 3, {})
        buyers, note = pumpfun.early_buyers(rpc, addr("hot"), lambda ts: 150.0, Criteria(), max_pages=3)
        self.assertEqual(buyers, [])
        self.assertIn("launch not reached", note)


class FomoTest(unittest.TestCase):
    def test_top50_snapshot_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "fomo.json"
            path.write_text(json.dumps({"wallets": [
                {"rank": 2, "handle": "bob", "pnl_usd": 2e5, "trades": 9, "solana": addr("bob"), "fomo_solana": None},
                {"rank": 1, "handle": "amy", "pnl_usd": 1e6, "trades": 40, "solana": addr("amy"),
                 "fomo_solana": addr("amy-app")}]}))
            with mock.patch.object(config, "FOMO_TOP50_FILE", path):
                rows = sources.fomo_top50()
        self.assertEqual([w for w, _ in rows], [addr("amy"), addr("amy-app"), addr("bob")])
        self.assertEqual(rows[0][1], "Fomo top-50 #1 @amy ($1.00M PnL, 40 trades)")
        self.assertTrue(rows[1][1].endswith("in-app wallet"))

    def test_bundled_snapshot_is_valid(self):
        rows = sources.fomo_top50()
        self.assertGreaterEqual(len(rows), 50)

    def test_trades_through_fomo_are_noted(self):
        wallet, mint = addr("fomo-user"), addr("coin")
        tx = rpc_tx(FOMO_SIGNER, "s1", 1, pre_tokens=[(USDC, 300_000_000, 6, wallet)],
                    post_tokens=[(USDC, 0, 6, wallet), (mint, 5, 0, wallet)])
        delta = delta_from_rpc_tx(tx, wallet)
        self.assertEqual(delta.fee_payer, FOMO_SIGNER)
        provider = RpcProvider.__new__(RpcProvider)
        provider.rpc = provider.helius = None
        provider.max_txs, provider.workers, provider.log = 100, 1, lambda *_: None
        provider.sol = mock.Mock(at=lambda ts: 150.0)
        with mock.patch("gemtracker.providers.fetch_history", return_value=History([delta], 1, True, "rpc")), \
                mock.patch("gemtracker.providers.token_quotes", return_value={}), \
                mock.patch("gemtracker.providers._verified_tokens", return_value={mint: {}}):
            report = provider.report(wallet)
        self.assertEqual(report.notes, ["1 trade(s) placed through the Fomo app"])
        self.assertEqual(report.positions[0].cost_usd, 300.0)
        self.assertTrue(report.positions[0].verified)


class CoinListTest(unittest.TestCase):
    def test_geckoterminal_fallback(self):
        m1, m2 = addr("pool-coin-1"), addr("pool-coin-2")
        pages = [{"data": [
            {"attributes": {"name": "AAA / SOL"}, "relationships": {"base_token": {"data": {"id": "solana_" + m1}}}},
            {"attributes": {"name": "BBB / SOL"}, "relationships": {"base_token": {"data": {"id": "solana_" + m2}}}},
            {"attributes": {"name": "AAA / USDC"}, "relationships": {"base_token": {"data": {"id": "solana_" + m1}}}},
        ]}, {"data": []}]

        def fake(url, params=None, headers=None):
            if "pump.fun" in url:
                raise sources.net.HttpError(403, url, "blocked")
            return pages[params["page"] - 1]
        with mock.patch.object(sources.net, "get_json", side_effect=fake), \
                mock.patch.object(config, "GEM_TOKENS_FILE", pathlib.Path("/nonexistent")):
            coins = sources.gem_coins_list(5, log=lambda *_: None)
        self.assertEqual(coins, [(m1, "AAA"), (m2, "BBB")])


class EarlySearchTest(unittest.TestCase):
    def test_only_wallets_early_on_several_coins_are_kept(self):
        w1, w2 = addr("w1"), addr("w2")
        results = {"A": ([(w1, 200.0, 1), (w2, 300.0, 1)], "note"), "B": ([(w1, 450.0, 2)], "note")}
        with mock.patch("gemtracker.pumpfun.early_buyers", side_effect=lambda rpc, mint, *a, **k: results[mint]), \
                mock.patch("gemtracker.prices.SolPrice"), mock.patch("gemtracker.solana.SolanaRpc"):
            book = CandidateBook()
            added = sources.early_search(book, [("A", "AAA"), ("B", "BBB")], Criteria(), 100, 2,
                                         log=lambda *_: None)
        self.assertEqual(added, 1)
        self.assertEqual(book.by_wallet[w1].early_hits, 2)
        self.assertNotIn(w2, book.by_wallet)

    def test_stops_when_out_of_time(self):
        with mock.patch("gemtracker.pumpfun.early_buyers") as early, \
                mock.patch("gemtracker.prices.SolPrice"), mock.patch("gemtracker.solana.SolanaRpc"):
            added = sources.early_search(CandidateBook(), [("A", "AAA")], Criteria(), 100, 2,
                                         log=lambda *_: None, deadline=0.0)
        self.assertEqual(added, 0)
        early.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class VerifiedTest(unittest.TestCase):
    def test_recent_gems_filter_and_mark(self):
        from gemtracker import verified, util
        from gemtracker.trades import Position
        now = util.now()
        tokens = {
            addr("gem"): {"symbol": "GEM", "mcap": 9e6, "launched_ts": now - 10 * 86400, "organic": 80, "tags": [],
                          "first_pool": addr("pool"), "launchpad": "met-dbc"},
            addr("old"): {"symbol": "OLD", "mcap": 9e9, "launched_ts": now - 900 * 86400, "organic": 90, "tags": []},
            addr("tiny"): {"symbol": "TINY", "mcap": 5e5, "launched_ts": now - 5 * 86400, "organic": 80, "tags": []},
            addr("usd"): {"symbol": "sUSDx", "mcap": 6e7, "launched_ts": now - 5 * 86400, "organic": 80, "tags": []},
            addr("lst"): {"symbol": "xSOL", "mcap": 6e7, "launched_ts": now - 5 * 86400, "organic": 80, "tags": ["lst"]},
        }
        self.assertEqual([m for m, _, _ in verified.recent_gems(tokens)], [addr("gem")])
        a, b = Position(addr("gem")), Position(addr("unknown"))
        verified.mark([a, b], tokens)
        self.assertEqual((a.verified, b.verified), (True, False))
        c = Position(addr("x"))
        verified.mark([c], None)
        self.assertIsNone(c.verified)
