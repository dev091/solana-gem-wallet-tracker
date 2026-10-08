"""Live dashboard (gemtracker/dashboard.py): incremental ledger reads, ET-day P&L, the local server."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from gemtracker import dashboard as D

ET = ZoneInfo("America/New_York")


def ms(*a):
    return int(datetime(*a, tzinfo=ET).timestamp() * 1000)


START = ms(2026, 10, 7, 20, 0)
MIN = 60_000


def fill(side, t, pnl=0.0, status="filled", algo="a"):
    return {"algo": algo, "side": side, "mint": "Mint1pump", "arrival_ms": t, "status": status, "reason": "x",
            "why": "", "sol": 0.2, "tx_fee_sol": 0.001, "sol_usd": 100.0, "pnl_sol": pnl, "mcap_sol": 40.0,
            "venue": "pump"}


def status(t, **eq):
    return {"t": t, "uptime_min": 1.0, "sol_usd": 100.0, "feed_lag_ms": {"pump": {"p50": 1500, "p90": 4800}},
            "algos": [{"algo": a, "equity_usd": v, "return": v / 100 - 1, "venue_fees_sol": 0.01,
                       "tx_fees_sol": 0.01} for a, v in eq.items()]}


class Dashboard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.write("config.json", {"started": START, "commit": "abc", "paper_only": True,
                                   "sim": {"start_usd": 100.0, "latency_ms": 2500}, "algos": ["a", "base_random"]})
        self.write("status.json", status(START + 3 * MIN, a=105.0, base_random=90.0))
        self.board = D.Board(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, obj):
        (self.dir / name).write_text(json.dumps(obj), encoding="utf-8")

    def append(self, name, *rows, raw=""):
        with open(self.dir / name, "a", encoding="utf-8") as fh:
            fh.write("".join(json.dumps(r) + "\n" for r in rows) + raw)

    def row(self, snap, algo="a"):
        return next(r for r in snap["algos"] if r["algo"] == algo)

    def test_need_daily_return_compounds_to_the_target(self):
        r = D.need_daily_return(100, 1500, 61)
        self.assertAlmostEqual(100 * (1 + r) ** 61 * r, 1500, delta=0.01)
        self.assertTrue(0.08 < r < 0.10)
        self.assertIsNone(D.need_daily_return(100, 1500, 0))

    def test_each_fill_counts_once_and_a_half_written_line_waits(self):
        late = json.dumps(fill("sell", START + 150_000, pnl=0.1))
        self.append("a.jsonl", fill("buy", START + MIN), fill("sell", START + 2 * MIN, pnl=0.05), raw=late[:20])
        r = self.row(self.board.snapshot(START + 4 * MIN))
        self.assertEqual((r["day_trips"], r["day_wins"], r["day_realized_usd"]), (1, 1, 5.0))
        self.append("a.jsonl", raw=late[20:] + "\n")
        self.board.snapshot(START + 4 * MIN)
        r = self.row(self.board.snapshot(START + 4 * MIN))
        self.assertEqual((r["day_trips"], r["day_realized_usd"]), (2, 15.0))

    def test_fills_of_an_earlier_run_in_the_same_ledger_are_ignored(self):
        self.append("a.jsonl", fill("sell", START - 60 * MIN, pnl=1.0), fill("sell", START + MIN, pnl=-0.02))
        snap = self.board.snapshot(START + 4 * MIN)
        self.assertEqual(self.row(snap)["day_trips"], 1)
        self.assertEqual([f["t"] for f in snap["recent"]], [START + MIN])

    def test_day_pnl_runs_from_the_last_equity_before_et_midnight(self):
        r = self.row(self.board.snapshot(START + 4 * MIN))           # run began today: opened at $100
        self.assertEqual((r["day_open_usd"], r["day_pnl_usd"], r["day_return"]), (100.0, 5.0, 0.05))
        self.append("summary.jsonl", {"t": ms(2026, 10, 7, 23, 30), "rows": [{"algo": "a", "equity_usd": 120.0}]})
        self.write("status.json", status(ms(2026, 10, 8, 0, 30), a=110.0, base_random=90.0))
        snap = self.board.snapshot(ms(2026, 10, 8, 0, 31))
        r = self.row(snap)
        self.assertEqual((r["day_open_usd"], r["day_pnl_usd"]), (120.0, -10.0))
        self.assertEqual(snap["today"], "2026-10-08")
        self.assertEqual(snap["curve"]["t"][0], START)
        self.assertEqual(snap["curve"]["series"]["a"][0], 100.0)
        self.assertEqual(snap["curve"]["series"]["a"][-1], 110.0)

    def test_a_new_run_starts_over(self):
        self.append("a.jsonl", fill("sell", START + MIN, pnl=0.05))
        self.assertEqual(self.row(self.board.snapshot(START + 4 * MIN))["day_trips"], 1)
        cfg = json.loads((self.dir / "config.json").read_text())
        self.write("config.json", {**cfg, "started": START + 2 * MIN})
        self.assertEqual(self.row(self.board.snapshot(START + 4 * MIN))["day_trips"], 0)

    def test_rows_by_equity_baselines_marked_recent_newest_first(self):
        self.append("a.jsonl", fill("buy", START + MIN), fill("sell", START + 2 * MIN, pnl=0.01))
        self.append("base_random.jsonl", fill("buy", START + 90_000, algo="base_random"))
        snap = self.board.snapshot(START + 4 * MIN)
        self.assertEqual([(r["algo"], r["baseline"]) for r in snap["algos"]], [("a", False), ("base_random", True)])
        self.assertEqual([f["t"] for f in snap["recent"]], [START + 2 * MIN, START + 90_000, START + MIN])
        self.assertEqual(snap["target_day_usd"], 1500)

    def test_server_serves_page_and_api_to_localhost_only(self):
        srv = D.make_server(self.board, 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            with urllib.request.urlopen(base + "/api", timeout=5) as r:
                self.assertEqual([a["algo"] for a in json.load(r)["algos"]], ["a", "base_random"])
            with urllib.request.urlopen(base + "/", timeout=5) as r:
                self.assertIn(b"Paper Desk", r.read())
            req = urllib.request.Request(base + "/api", headers={"Host": "evil.example"})
            with self.assertRaises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(e.exception.code, 403)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_stop_file_shuts_the_server_down_and_is_removed(self):
        srv = D.make_server(self.board, 0)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        stop = self.dir / D.STOP_FILE
        stop.touch()
        D.watch_stop(srv, stop, every_s=0.01)
        th.join(5)
        srv.server_close()
        self.assertFalse(th.is_alive())
        self.assertFalse(stop.exists())

    def test_recent_keeps_algo_fills_when_baselines_are_busy(self):
        self.append("a.jsonl", fill("buy", START + MIN))
        self.append("base_random.jsonl", *[fill("buy", START + 2 * MIN + i, algo="base_random")
                                           for i in range(D.RECENT_FILLS + 5)])
        recent = self.board.snapshot(START + 4 * MIN)["recent"]
        self.assertEqual(len(recent), D.RECENT_FILLS + 1)
        self.assertEqual([(f["algo"], f["baseline"]) for f in recent if not f["baseline"]], [("a", False)])


if __name__ == "__main__":
    unittest.main()
