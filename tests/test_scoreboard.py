"""Scoreboard: ET day boundaries, elite and algo PnL booking, rolling window and ranking."""
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from gemtracker.scoreboard import algo_days, board, elite_days, et_day


def ms(*a):
    return int(datetime(*a, tzinfo=timezone.utc).timestamp() * 1000)


class EtDayTest(unittest.TestCase):
    def test_edt_and_est_boundaries(self):
        self.assertEqual(et_day(ms(2026, 10, 8, 3, 59)), date(2026, 10, 7))   # 11:59 PM EDT
        self.assertEqual(et_day(ms(2026, 10, 8, 4, 0)), date(2026, 10, 8))
        self.assertEqual(et_day(ms(2026, 12, 1, 4, 59)), date(2026, 11, 30))  # 11:59 PM EST
        self.assertEqual(et_day(ms(2026, 12, 1, 5, 0)), date(2026, 12, 1))
        # DST ends Sunday 2026-11-01 at 2 AM EDT (06:00 UTC)
        self.assertEqual(et_day(ms(2026, 11, 2, 4, 30)), date(2026, 11, 1))


class BoardTest(unittest.TestCase):
    def test_books_pnl_fees_and_ranks_by_return_per_sol(self):
        with tempfile.TemporaryDirectory() as d:
            prof, run = Path(d) / "profiles", Path(d) / "run"
            prof.mkdir()
            run.mkdir()
            trips = [{"open_rx": ms(2026, 10, 7, 18), "hold_s": 10, "sol_in": 10.0, "sol_out": 12.0},
                     {"open_rx": ms(2026, 10, 7, 19), "hold_s": 10, "sol_in": 10.0, "sol_out": 9.0}]
            (prof / "Decu.trips.jsonl").write_text("".join(json.dumps(t) + "\n" for t in trips))
            t0 = ms(2026, 10, 7, 18)
            fills = [{"side": "buy", "status": "filled", "sol": 0.5, "pnl_sol": 0, "tx_fee_sol": 0.001,
                      "arrival_ms": t0, "sol_usd": 100.0},
                     {"side": "sell", "status": "filled", "sol": 0.7, "pnl_sol": 0.198, "tx_fee_sol": 0.001,
                      "arrival_ms": t0 + 5000, "sol_usd": 100.0},
                     {"side": "buy", "status": "rejected", "sol": 0, "pnl_sol": 0, "tx_fee_sol": 0.001,
                      "arrival_ms": t0 + 9000, "sol_usd": 100.0}]
            (run / "decu.jsonl").write_text("".join(json.dumps(f) + "\n" for f in fills))
            (run / "summary.jsonl").write_text('{"ignored": true}\n')
            rows = elite_days(prof, 100.0) | algo_days(run)
            res = {r["entity"]: r for r in board(rows, 30)}
        self.assertEqual(set(res), {"Decu", "decu"})
        self.assertAlmostEqual(res["Decu"]["window_sol"], 1.0)
        self.assertAlmostEqual(res["Decu"]["return_per_sol"], 0.05)
        self.assertEqual((res["Decu"]["trips"], res["Decu"]["win_rate"]), (2, 0.5))
        self.assertAlmostEqual(res["decu"]["window_sol"], 0.197)   # rejected order still paid its fee
        self.assertAlmostEqual(res["decu"]["return_per_sol"], 0.394)
        self.assertAlmostEqual(res["decu"]["on_start"], 0.197)
        self.assertEqual(board(rows, 30)[0]["entity"], "decu")

    def test_window_excludes_old_days(self):
        rows = {("a", date(2026, 9, 1)): {"entity": "a", "kind": "algo", "pnl_sol": 5.0, "pnl_usd": 500.0,
                                          "deployed_sol": 1.0, "trips": 1, "wins": 1},
                ("a", date(2026, 10, 7)): {"entity": "a", "kind": "algo", "pnl_sol": 1.0, "pnl_usd": 100.0,
                                           "deployed_sol": 1.0, "trips": 1, "wins": 1}}
        (r,) = board(rows, 30, today=date(2026, 10, 7))
        self.assertEqual((r["window_usd"], r["today_usd"], r["gap_today_usd"]), (100.0, 100.0, 1400.0))   # $1.5k target - $100


if __name__ == "__main__":
    unittest.main()
