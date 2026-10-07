import pathlib
import tempfile
import unittest
from unittest import mock

from gemtracker import leaderboard as lb
from gemtracker import net
from tests.helpers import addr

W = [addr(f"lb{i}") for i in range(6)]

KOLSCAN_ROW = (
    '<a style="display:flex" href="/account/{w}?timeframe=1"><div></div>'
    '<h1 style="font-size:20px">{name}</h1></a><p class="cursor-pointer remove-mobile">x</p>'
    '<div class="remove-mobile"><p style="color:var(--buy-color);margin-right:2px">{wins}</p>/'
    '<p style="color:var(--sell-color);margin-left:2px">{losses}</p></div>'
    '<div class="leaderboard_totalProfitNum__HzfFO"><h1>{sol}<!-- --> <!-- -->Sol</h1>'
    '<h1>(<!-- -->${usd}<!-- -->)</h1></div>')


def kolscan_page(rows):
    shell = f'<html><a href="/account/{W[5]}">nav link, not a board row</a>'
    return shell + '<div hidden id="S:0">' + "".join(KOLSCAN_ROW.format(**r) for r in rows) + "</div>"


def pump_reply(n):
    return {"entries": [{"rank": i + 1, "walletAddress": W[i], "pnlUsd": 50_000 - i * 10_000, "pnlSol": 400 - i * 80,
                         "realizedPnlUsd": 1.0, "buySpendSol": 5.0 + i, "pnlPercent": 900.0 - i * 100,
                         "positionsCount": 3, "username": f"user{i}"} for i in range(n)],
            "periodType": 3, "periodLabel": "24h", "windowStartSec": 0}


class ParseTest(unittest.TestCase):
    def test_kolscan_rows(self):
        page = kolscan_page([dict(w=W[0], name="xander", wins=5, losses=20, sol="+595.34", usd="69,276.4"),
                             dict(w=W[1], name="Jo &amp; Co", wins=1, losses=0, sol="-1.5", usd="-170")])
        rows = lb.parse_kolscan(page)
        self.assertEqual([(r.rank, r.wallet, r.name) for r in rows], [(1, W[0], "xander"), (2, W[1], "Jo & Co")])
        self.assertEqual((rows[0].wins, rows[0].losses, rows[0].pnl_sol, rows[0].pnl_usd), (5, 20, 595.34, 69276.4))
        self.assertEqual(rows[1].pnl_usd, -170.0)

    def test_pump_board_and_ladder(self):
        with mock.patch.object(net, "get_json", return_value=pump_reply(5)) as get:
            rows = lb.pump_board("daily")
        self.assertEqual(get.call_args.kwargs["params"], {"period": "daily", "limit": 100})
        self.assertEqual([r.rank for r in rows], [1, 2, 3, 4, 5])
        self.assertEqual(rows[0].board, "pump.fun daily")
        self.assertEqual(lb.ladder(rows), {"1": 50000.0, "5": 10000.0})


class HistoryTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        for name, value in (("HISTORY_FILE", root / "h.json"), ("SEEN_FILE", root / "s.json"),
                            ("DASHBOARD_FILE", root / "d.json")):
            patcher = mock.patch.object(lb, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def snapshot(self, ts, daily_wallets, weekly_wallets=()):
        def rows(board, wallets):
            return [lb.BoardRow(board, i + 1, w, f"n{i}", pnl_usd=1000.0 * (10 - i), spent_sol=2.0, roi_pct=500.0)
                    for i, w in enumerate(wallets)]
        boards = {"pump.fun daily": rows("pump.fun daily", daily_wallets)}
        if weekly_wallets:
            boards["pump.fun weekly"] = rows("pump.fun weekly", weekly_wallets)
        return {"ts": ts, "boards": boards, "errors": {}}

    def test_repeat_leaders_count_days_and_boards(self):
        day = 86400
        lb.record(self.snapshot(1_000 * day, [W[0], W[1]]))
        lb.record(self.snapshot(1_000 * day + 3600, [W[0], W[1]]))       # same day: no extra credit
        snap = self.snapshot(1_001 * day, [W[0], W[2]], weekly_wallets=[W[0]])
        history, seen = lb.record(snap)
        self.assertEqual(len(history), 3)
        leaders = lb.repeat_leaders(snap, seen)
        self.assertEqual(leaders[0]["wallet"], W[0])
        self.assertEqual(leaders[0]["days_on_daily_board"], 2)
        self.assertEqual(leaders[0]["boards_now"], ["pump.fun daily", "pump.fun weekly"])
        self.assertNotIn(W[2], [r["wallet"] for r in leaders])      # one appearance is not consistency
        payload = lb.save_dashboard(snap, history, seen)
        self.assertEqual(payload["history"][-1]["pump_daily_5"], None)  # fewer than 5 rows
        self.assertTrue(lb.DASHBOARD_FILE.with_suffix(".js").exists())

    def test_wallet_standing(self):
        snap = self.snapshot(1, [W[0], W[1], W[2], W[3], W[4]])
        standing = {name: (rank, cutoff) for name, rank, _, cutoff, _ in lb.wallet_standing(snap, W[1])}
        self.assertEqual(standing["pump.fun daily"], (2, 6000.0))
        missing = lb.wallet_standing(snap, W[5])[0]
        self.assertIsNone(missing[1])


if __name__ == "__main__":
    unittest.main()
