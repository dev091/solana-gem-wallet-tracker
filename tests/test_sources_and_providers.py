import unittest
from unittest import mock

from gemtracker import net, sources, util
from gemtracker.config import Criteria
from gemtracker.providers import position_from_solanatracker
from gemtracker.sources import CandidateBook
from tests.helpers import addr

W1, W2, W3 = addr("w1"), addr("w2"), addr("w3")


class UtilTest(unittest.TestCase):
    def test_addresses(self):
        self.assertTrue(util.is_address("So11111111111111111111111111111111111111112"))
        self.assertTrue(util.is_address(W1))
        for bad in ("", "abc", "0" * 44, W1[:-6], None, 123):
            self.assertFalse(util.is_address(bad), bad)

    def test_seconds_and_redaction(self):
        self.assertEqual(util.to_seconds(1_700_000_000_000), 1_700_000_000)
        self.assertEqual(util.to_seconds(1_700_000_000), 1_700_000_000)
        self.assertIsNone(util.to_seconds(None))
        self.assertEqual(net.redact("https://x.io/?api-key=SECRET&limit=5"), "https://x.io/?api-key=***&limit=5")
        self.assertEqual(net.redact("https://api.telegram.org/bot123:ABC/sendMessage"),
                         "https://api.telegram.org/bot***/sendMessage")

    def test_wallet_list_file(self):
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "seeds.txt"
            path.write_text(f"# comment\n{W1}  Fomo 7d #1 @frank\n\nnot-an-address\n{W2}\n")
            self.assertEqual(util.read_wallet_list(path), [(W1, "Fomo 7d #1 @frank"), (W2, "")])


class CandidateBookTest(unittest.TestCase):
    def test_merge_and_priority(self):
        book = CandidateBook()
        book.add(W1, "kolscan", "Kolscan #1")
        book.add(W2, "seeds", "mine")
        book.add(W3, "kolscan", "Kolscan #2")
        book.add(W3, "fomo", "Fomo 24h #4")
        book.add(W1, "gem-search", "X").gem_hits += 2
        self.assertIsNone(book.add("bogus", "kolscan"))
        self.assertEqual([c.wallet for c in book.ordered()], [W1, W2, W3])
        again = CandidateBook.from_list(book.to_list())
        self.assertEqual(again.by_wallet[W1].gem_hits, 2)
        self.assertEqual(again.by_wallet[W3].sources, ["kolscan", "fomo"])


class SourceParsingTest(unittest.TestCase):
    def test_kolscan_scrape(self):
        html = f'<a href="/account/{W1}">Cented</a><a href="/account/{W2}">x</a><a href="/account/{W1}">dup</a>'
        with mock.patch.object(net, "get_text", return_value=html):
            self.assertEqual(sources.kolscan(10), [(W1, "Kolscan/Pump.fun leaderboard #1"),
                                                   (W2, "Kolscan/Pump.fun leaderboard #2")])
        with mock.patch.object(net, "get_text", return_value="<html></html>"):
            with self.assertRaises(sources.SourceError):
                sources.kolscan(10)

    def test_fomo_leaderboard(self):
        reply = {"data": {"traders": [
            {"rank": 1, "handle": "frank", "wallets": {"solana": W1, "evm": "0xabc"}},
            {"rank": 2, "handle": "nowallet", "wallets": {}},
        ]}}
        with mock.patch.object(net, "get_json", return_value=reply) as get:
            rows = sources.fomo(10, "KEY")
        self.assertEqual(rows[0], (W1, "Fomo 24h #1 @frank"))
        self.assertEqual(len(rows), 3)  # once per window (24h, 7d, 30d)
        self.assertEqual(get.call_args.kwargs["headers"], {"authorization": "Bearer KEY"})
        with self.assertRaises(sources.SourceError):
            sources.fomo(10, "")

    def test_gmgn_wallet_feeds(self):
        reply = {"code": 0, "data": {"list": [
            {"maker": W1, "maker_info": {"twitter_username": "alpha"}},
            {"maker": W1}, {"maker": W2, "maker_info": {}}]}}
        with mock.patch.object(net, "get_json", return_value=reply):
            rows = sources.gmgn(10, "KEY")
        self.assertIn((W1, "GMGN smart money @alpha"), rows)
        self.assertIn((W2, "GMGN KOL"), rows)
        with mock.patch.object(net, "get_json", return_value={"code": 40001, "message": "bad key"}):
            with self.assertRaises(sources.SourceError):
                sources.gmgn(10, "KEY")

    def test_gem_search_counts_coins_per_wallet(self):
        def fake(url, params=None, headers=None):
            mint = url.split("/tokens/")[1].split("/")[0]
            traders = {
                "A": [{"wallet": W1, "invested": 250, "pnl": {"token": {"realized": 400_000}}},
                      {"wallet": W2, "invested": 5_000, "pnl": {"token": {"realized": 300_000}}},  # entry too big
                      {"wallet": W3, "invested": 300, "pnl": {"token": {"realized": 150_000}},
                       "identity": {"type": "bot"}},
                      {"wallet": W2, "invested": 200, "pnl": {"token": {"realized": 50_000}}}],      # too little
                "B": [{"wallet": W1, "invested": 480, "pnl": {"token": {"realized": 101_000}}}],
            }[mint[-1]]
            return {"traders": traders}
        book = CandidateBook()
        coins = [(addr("coin") + "A", "AAA"), (addr("coin") + "B", "BBB")]
        with mock.patch.object(net, "get_json", side_effect=fake):
            added = sources.gem_search(book, coins, Criteria(), "KEY", "", log=lambda *_: None)
        self.assertEqual(added, 2)
        self.assertEqual(list(book.by_wallet), [W1])
        self.assertEqual(book.by_wallet[W1].gem_hits, 2)
        with self.assertRaises(sources.SourceError):
            sources.gem_search(book, coins, Criteria(), "", "")

    def test_pumpfun_top_coins(self):
        m = addr("pumpcoin")
        with mock.patch.object(net, "get_json", return_value=[{"mint": m, "symbol": "PEPE"}, {"mint": "x"}]):
            self.assertEqual(sources.pumpfun_top_coins(5), [(m, "PEPE")])


class SolanaTrackerMappingTest(unittest.TestCase):
    def test_position_fields(self):
        row = {"token": W1, "invested": 312.5, "proceeds": 140_000, "pnl": {"realized": 139_687.5},
               "current": {"balance": 10.0, "value": 55.0, "price": 5.5},
               "volume": {"tokensBought": 1000, "tokensSold": 990},
               "counts": {"buys": 2, "sells": 3}, "timing": {"firstBuy": 1_700_000_000_000, "lastTrade": 1_700_100_000_000},
               "meta": {"symbol": "GEM", "liquidity": 90_000}}
        p = position_from_solanatracker(row)
        self.assertEqual((p.symbol, p.cost_usd, p.proceeds_usd, p.value_usd), ("GEM", 312.5, 140_000, 55.0))
        self.assertEqual((p.buys, p.sells, p.first_buy_ts), (2, 3, 1_700_000_000))
        self.assertAlmostEqual(p.multiple, (140_000 + 55) / 312.5)
        self.assertEqual(p.transfer_in, 0)

        received = position_from_solanatracker({"token": W2, "invested": 0, "proceeds": 9_000,
                                                "volume": {"tokensBought": 0, "tokensSold": 500}})
        self.assertEqual(received.transfer_in, 500)


if __name__ == "__main__":
    unittest.main()
