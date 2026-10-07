import json
import pathlib
import tempfile
import unittest
from unittest import mock

from gemtracker import alerts, config, paper, scan, watch
from gemtracker.config import Criteria
from gemtracker.criteria import WalletReport
from gemtracker.prices import TokenQuote
from gemtracker.sources import Candidate
from gemtracker.trades import Position
from tests.helpers import SOL, addr, rpc_tx
from tests.test_solana import FakeRpc

NOW = 1_760_000_000
W_GOOD, W_BAD, W_BROKEN = addr("good"), addr("bad"), addr("broken")


class FixedSol:
    def at(self, _ts):
        return 150.0


def gem(i):
    return Position(addr(f"g{i}"), symbol=f"G{i}", cost_usd=300, proceeds_usd=200_000, buys=1, sells=1,
                    first_buy_ts=NOW - 40 * 86400)


class FakeProvider:
    name = "fake"

    def describe(self):
        return "fake"

    def report(self, wallet):
        if wallet == W_BROKEN:
            raise RuntimeError("rpc down")
        positions = [gem(i) for i in range(5 if wallet == W_GOOD else 1)]
        return WalletReport(wallet, positions, tx_count=20, source="fake")


class TempDirs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        patches = [mock.patch.object(config, "DATA_DIR", root / "data"),
                   mock.patch.object(config, "DOCS_DATA_DIR", root / "docs"),
                   mock.patch.object(config, "WATCHLIST_FILE", root / "watchlist.txt"),
                   mock.patch.object(watch, "STATE_FILE", root / "data" / "watch_state.json"),
                   mock.patch.object(watch, "ACTIVITY_FILE", root / "docs" / "activity.json"),
                   mock.patch.object(watch, "HOLDINGS_FILE", root / "data" / "holdings.json"),
                   mock.patch.object(watch, "LEADERBOARD_FILE", root / "docs" / "leaderboard.json"),
                   mock.patch.object(paper, "LEDGER_FILE", root / "data" / "paper.json"),
                   mock.patch.object(paper, "DASHBOARD_FILE", root / "docs" / "paper.json")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()


class ScanTest(TempDirs):
    def test_scan_sorts_saves_and_lists_tracked(self):
        cands = [Candidate(W_BAD, ["Kolscan #1"], ["kolscan"]), Candidate(W_BROKEN, [], ["seeds"]),
                 Candidate(W_GOOD, ["Fomo 7d #2"], ["fomo"])]
        with mock.patch("time.time", return_value=NOW):
            results = scan.scan(cands, FakeProvider(), Criteria(), max_wallets=10, log=lambda *_: None)
        self.assertEqual([r["tier"] for r in results], ["STRICT", "REJECTED", "ERROR"])
        self.assertEqual(results[0]["wallet"], W_GOOD)
        self.assertEqual(len(results[0]["gems"]), 5)

        payload = scan.save_results(results, Criteria(), "fake", {"fomo": {"ok": True}})
        self.assertEqual(payload["counts"], {"scanned": 3, "strict": 1, "gem_hunter": 0, "rejected": 1, "error": 1})
        js = (self.root / "docs" / "wallets.js").read_text()
        self.assertTrue(js.startswith("window.GEM_WALLETS = {"))
        tracked = json.loads((self.root / "data" / "tracked.json").read_text())["wallets"]
        self.assertEqual([t["wallet"] for t in tracked], [W_GOOD])


class WatchTest(TempDirs):
    def test_first_poll_starts_quietly_then_reports_buys(self):
        mint = addr("newcoin")
        (self.root / "data").mkdir()
        (self.root / "data" / "tracked.json").write_text(json.dumps(
            {"wallets": [{"wallet": W_GOOD, "tier": "STRICT", "label": "Fomo 7d #2", "gems": 5}]}))
        (self.root / "watchlist.txt").write_text(f"{W_GOOD} dup\n")
        wallets = watch.tracked_wallets()
        self.assertEqual(len(wallets), 1)

        buy = rpc_tx(W_GOOD, "buy-sig", NOW, sol_before=10 * SOL, sol_after=8 * SOL,
                     post_tokens=[(mint, 5_000_000, 6)])
        rpc = FakeRpc([[{"signature": "old", "err": None}],
                       [{"signature": "buy-sig", "err": None}]], {"buy-sig": buy})
        w = watch.Watcher(rpc, FixedSol(), log=lambda *_: None, mode="txs")
        quotes = {mint: TokenQuote(mint, "NEW", price=0.0001, liquidity=20_000, market_cap=90_000)}
        with mock.patch.object(watch, "token_quotes", return_value=quotes), \
                mock.patch.object(alerts, "enabled", return_value=True), \
                mock.patch.object(alerts, "send") as send:
            self.assertEqual(w.run_once(wallets), [])           # first look: no backlog alerts
            self.assertEqual(w.state["last_sig"][W_GOOD], "old")
            events = w.run_once(wallets)
        self.assertEqual(len(events), 1)
        e = events[0]
        self.assertEqual((e["side"], e["symbol"], e["usd"], e["sol"]), ("buy", "NEW", 300.0, 2.0))
        self.assertEqual(w.state["last_sig"][W_GOOD], "buy-sig")
        first_line = send.call_args.args[0][0][0]
        self.assertIn("BUY NEW", first_line)
        activity = (self.root / "docs" / "activity.js").read_text()
        self.assertIn("buy-sig", activity)

    def test_consensus_when_two_tracked_wallets_buy_same_coin(self):
        w = watch.Watcher(FakeRpc([], {}), FixedSol(), log=lambda *_: None, mode="txs")
        mint = addr("hot")
        ev = {"side": "buy", "mint": mint, "symbol": "HOT"}
        with mock.patch.object(alerts, "enabled", return_value=True), mock.patch.object(alerts, "send") as send, \
                mock.patch("gemtracker.util.now", return_value=NOW):
            w._update_consensus([{**ev, "wallet": W_GOOD, "ts": NOW - 60}, {**ev, "wallet": W_BAD, "ts": NOW}])
            w._update_consensus([])  # no repeat alert
        self.assertEqual(len(w.consensus), 1)
        self.assertEqual(send.call_count, 1)
        self.assertIn("2 tracked wallets bought HOT", send.call_args.args[0][0][0])


if __name__ == "__main__":
    unittest.main()


class HoldingsWatchTest(TempDirs):
    def test_holdings_diff_finds_buys_and_sells_and_paper_trades_them(self):
        gem, spam, gone = addr("gem-coin"), addr("spam-airdrop"), addr("sold-coin")
        snapshots = [
            {gone: 1000.0},                                   # baseline
            {gone: 1000.0, gem: 5000.0, spam: 1e9},           # bought GEM, got airdropped spam
            {gem: 5000.0, spam: 1e9},                         # sold everything of `gone`
            {spam: 1e9},                                      # sold GEM
        ]
        prices = [{gem: 0.01, gone: 0.5}, {gem: 0.01, gone: 0.5, spam: 0.0}, {gem: 0.03, gone: 0.6},
                  {gem: 0.05}]
        wallets = [{"wallet": W_GOOD, "label": "consistent decu", "tier": "BOARD"}]
        w = watch.Watcher(FakeRpc([], {}), FixedSol(), log=lambda *_: None, mode="holdings")
        calls = {"n": 0}

        def fake_holdings(rpc, wallet):
            return dict(snapshots[calls["n"]])

        def fake_quotes(mints, log=None):
            table = prices[calls["n"]]
            out = {}
            for m in mints:
                if m in table:
                    liq = 10.0 if m == spam else 50_000.0
                    out[m] = TokenQuote(m, "GEM" if m == gem else "X", price=table[m], liquidity=liq)
            return out

        with mock.patch.object(watch, "fetch_holdings", side_effect=fake_holdings), \
                mock.patch.object(watch, "token_quotes", side_effect=fake_quotes), \
                mock.patch.object(alerts, "enabled", return_value=False):
            rounds = []
            for i in range(4):
                calls["n"] = i
                rounds.append([(e["side"], e["symbol"]) for e in w.run_once(wallets)])
        self.assertEqual(rounds[0], [])                       # baseline
        self.assertEqual(rounds[1], [("buy", "GEM")])         # spam airdrop ignored (no liquidity)
        self.assertEqual(rounds[2], [("sell", "X")])          # sold a coin bought before tracking
        self.assertEqual(rounds[3], [("sell", "GEM")])
        closed = w.paper.closed
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["reason"], "wallet sold")
        # entered at 0.01, exited at 0.05: 5x minus 2% fee on each side
        self.assertAlmostEqual(closed[0]["returns"]["mirror"], 0.98 * 0.98 * 5, places=4)
        self.assertTrue((self.root / "docs" / "paper.js").exists())


class PaperBookTest(TempDirs):
    def test_policies_and_expiry(self):
        book = paper.PaperBook(stake=20, fee_pct=0)
        t0 = 1_000_000
        book.on_buy({"wallet": W_GOOD, "mint": "A", "price": 1.0}, t0)
        self.assertIsNone(book.on_buy({"wallet": W_GOOD, "mint": "A", "price": 1.1}, t0))  # no duplicates
        book.on_buy({"wallet": W_BAD, "mint": "B", "price": 1.0}, t0)
        book.mark({"A": 3.0, "B": 0.5}, t0 + 3600)           # A ran to 3x
        book.mark({"A": 0.5, "B": 0.4}, t0 + 25 * 3600)      # 24h prices recorded
        book.on_sell(W_GOOD, "A", 0.5, t0 + 26 * 3600)       # wallet dumped A at 0.5
        book.mark({"B": 0.0}, t0 + 49 * 3600)                # B dead, closed at the 48h limit
        a, b = book.closed
        self.assertEqual(a["returns"], {"mirror": 0.5, "tp2x_half": 1.25, "hold_24h": 0.5})
        self.assertEqual(b["reason"], "48h limit")
        self.assertEqual(b["returns"]["mirror"], 0.0)
        s = book.summary()["overall"]
        self.assertEqual(s["trades"], 2)
        self.assertEqual(s["tp2x_half"]["pnl_usd"], round((0.25 - 1) * 20, 2))  # +5 on A, -20 on B
