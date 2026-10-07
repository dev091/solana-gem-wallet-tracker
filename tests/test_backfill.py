import gzip
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from gemtracker import backfill as bf
from gemtracker.chain_events import WSOL, _price
from gemtracker.market import Market
from gemtracker.replay import row_to_event
from gemtracker.scoreboard import et_day

K = bf.PUMP_V_SOL * bf.PUMP_V_TOKENS
MINT = "Mint1111111111111111111111111111111111pump"


def ms(y, mo, d, h, mi=0, s=0):
    return int(datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp() * 1000)


class Curve:
    """A pump curve that emits Slinky21-style trade rows."""

    def __init__(self, mint=MINT):
        self.mint, self.vq, self.vb = mint, bf.PUMP_V_SOL, bf.PUMP_V_TOKENS

    def trade(self, ix, tokens, t_ms, slot, tx, sig):
        if ix.startswith("buy"):
            self.vb -= tokens
            new_vq = K // self.vb
            sol, self.vq = new_vq - self.vq, new_vq
        else:
            self.vb += tokens
            new_vq = K // self.vb
            sol, self.vq = self.vq - new_vq, new_vq
        return {"block_time": t_ms * 1000, "slot": slot, "tx_index": tx, "signature": sig,
                "mint": self.mint, "trade_user": "user" + sig, "creator": "creator",
                "ix_name": ix, "sol_amount": sol, "token_amount": tokens,
                "virtual_sol_reserves": self.vq, "virtual_token_reserves": self.vb,
                "real_sol_reserves": self.vq - bf.PUMP_V_SOL,
                "real_token_reserves": self.vb - (bf.PUMP_V_TOKENS - bf.PUMP_INITIAL_REAL_TOKENS),
                "fee_basis_points": 95, "creator_fee_basis_points": 30}


def write_parquet(path: Path, rows: list[dict], row_group_size=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    table = pa.Table.from_pandas(df, preserve_index=False)
    table = table.set_column(table.schema.get_field_index("block_time"), "block_time",
                             pa.array(df["block_time"].astype("int64"), pa.int64())
                             .cast(pa.timestamp("us", tz="UTC")))
    pq.write_table(table, path, row_group_size=row_group_size)


def create_row(t_ms, slot, tx, sig, mint=MINT):
    return {"block_time": t_ms * 1000, "slot": slot, "tx_index": tx, "signature": sig,
            "mint": mint, "bonding_curve": "curve", "creator": "creator", "tx_signer": "dev",
            "token_name": "Coin", "symbol": "C", "is_mayhem_mode": False,
            "token_total_supply": 10 ** 15, "virtual_sol_reserves": bf.PUMP_V_SOL,
            "virtual_token_reserves": bf.PUMP_V_TOKENS}


def read_rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(x) for x in fh]


class TmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class SlinkyTest(TmpDir):
    day = date(2026, 8, 20)        # EDT: the ET day starts 04:00 UTC

    def convert(self, creates, trades, grads=()):
        base = self.dir / "src"
        write_parquet(base / "p" / "a" / "create" / "c1.parquet", creates)
        for i, part in enumerate(trades):
            write_parquet(base / "p" / "a" / "trade" / f"t{i}.parquet", part)
        if grads:
            write_parquet(base / "p" / "a" / "graduate" / "g1.parquet", list(grads))
        index = bf.SlinkyIndex(base, stable_s=0)
        out = self.dir / "out"
        man = bf.convert_slinky_day(self.day, index, out, lag_ms=1400)
        return read_rows(bf.tape_path(out, "slinky21", self.day)), man

    def test_rows_ordered_by_slot_then_tx_index_with_monotone_rx(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy", 10 ** 12, t, 100, 5, "a"), c.trade("buy", 10 ** 12, t, 100, 9, "b"),
                c.trade("sell", 10 ** 11, t, 101, 1, "c"), c.trade("buy", 10 ** 12, t + 1000, 103, 0, "d")]
        out, man = self.convert([create_row(t, 100, 2, "z")], [rows[::-1]])
        self.assertEqual([r["sig"] for r in out], ["z", "a", "b", "c", "d"])
        self.assertEqual(out[0]["k"], "create")
        rx = [r["rx"] for r in out]
        self.assertEqual(rx, sorted(rx))
        self.assertGreater(out[3]["rx"], out[2]["rx"])  # a later slot inside the same second
        self.assertTrue(all(t + 1400 <= r["rx"] < t + 2400 for r in out[:4]))
        self.assertEqual(man["rows"], 5)
        self.assertEqual(man["rx_out_of_order"], 0)
        self.assertIn("PumpSwap", man["no_pumpswap"])

    def test_duplicates_across_overlapping_files_are_dropped_once(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy", 10 ** 12, t + i * 1000, 100 + 3 * i, 0, f"s{i}") for i in range(4)]
        out, man = self.convert([create_row(t, 99, 0, "z")], [rows, rows[2:]])
        self.assertEqual([r["sig"] for r in out if r["k"] == "trade"], ["s0", "s1", "s2", "s3"])
        self.assertEqual(man["dropped"]["duplicate_trade"], 2)

    def test_files_with_different_int_widths_are_read_together(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy", 10 ** 12, t + i * 1000, 100 + 3 * i, i, f"s{i}") for i in range(4)]
        base = self.dir / "src"
        write_parquet(base / "p" / "a" / "create" / "c1.parquet", [create_row(t, 99, 0, "z")])
        write_parquet(base / "p" / "a" / "trade" / "t0.parquet", rows[:2])
        table = pq.read_table(base / "p" / "a" / "trade" / "t0.parquet")
        write_parquet(base / "p" / "a" / "trade" / "t1.parquet", rows[2:])
        t1 = pq.read_table(base / "p" / "a" / "trade" / "t1.parquet")
        i = t1.schema.get_field_index("tx_index")
        pq.write_table(t1.set_column(i, "tx_index", t1.column(i).cast(pa.int32())),
                       base / "p" / "a" / "trade" / "t1.parquet")
        self.assertEqual(table.schema.field("tx_index").type, pa.int64())
        man = bf.convert_slinky_day(self.day, bf.SlinkyIndex(base, stable_s=0), self.dir / "out")
        self.assertEqual(man["rows_by_kind"]["trade"], 4)

    def test_side_comes_from_ix_name(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy_exact_sol_in", 10 ** 12, t, 100, 0, "a"),
                c.trade("buy_exact_quote_in", 10 ** 12, t, 101, 0, "b"),
                c.trade("buy", 10 ** 12, t, 102, 0, "c"), c.trade("sell", 10 ** 12, t, 103, 0, "d")]
        out, _ = self.convert([create_row(t, 99, 0, "z")], [rows])
        trades = [r for r in out if r["k"] == "trade"]
        self.assertEqual([r["side"] for r in trades], ["buy", "buy", "buy", "sell"])
        self.assertEqual(trades[0]["fee"], 125)
        self.assertNotIn("qm", trades[0])

    def test_same_tx_trades_follow_the_curve_chain(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        first, second = c.trade("buy", 10 ** 12, t, 100, 3, "x"), c.trade("sell", 5 * 10 ** 11, t, 100, 3, "x")
        out, _ = self.convert([create_row(t, 99, 0, "z")], [[second, first]])
        trades = [r for r in out if r["k"] == "trade"]
        self.assertEqual([r["side"] for r in trades], ["buy", "sell"])

    def test_day_split_on_eastern_midnight(self):
        c = Curve()
        before, after = ms(2026, 8, 20, 3, 59, 59), ms(2026, 8, 20, 4)
        rows = [c.trade("buy", 10 ** 12, before, 100, 0, "late"), c.trade("buy", 10 ** 12, after, 110, 0, "early")]
        out, man = self.convert([create_row(before, 99, 0, "z")], [rows])
        self.assertEqual([r["sig"] for r in out], ["early"])
        self.assertEqual(bf.et_bounds(self.day), (after, ms(2026, 8, 21, 4)))
        self.assertEqual(bf.et_bounds(date(2026, 11, 10))[0], ms(2026, 11, 10, 5))  # EST
        self.assertEqual(et_day(after), self.day)
        self.assertEqual(et_day(before), date(2026, 8, 19))

    def test_graduation_is_emitted_as_live_migrate_and_pool(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy", 10 ** 12, t, 100, 0, "a")]
        grad = {"block_time": (t + 1000) * 1000, "slot": 103, "tx_index": 1, "signature": "g",
                "mint": MINT, "pool": "Pool1", "triggered_by": "bot", "mint_amount": 206_900_000 * 10 ** 6,
                "sol_amount": 84_990_362_158}
        out, _ = self.convert([create_row(t, 99, 0, "z")], [rows], [grad])
        mig, pool = out[-2], out[-1]
        self.assertEqual((mig["k"], mig["v"], mig["u"], mig["pg"]), ("migrate", "pump", "bot", 1.0))
        self.assertEqual((pool["k"], pool["v"], pool["pool"], pool["mint"]), ("pool", "pumpswap", "Pool1", MINT))
        self.assertAlmostEqual(pool["px"], _price(84_990_362_158, 206_900_000 * 10 ** 6))
        self.assertEqual(pool["x"], {"base_decimals": 6})

    def test_market_price_after_replay_matches_reserves(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy" if i % 3 else "sell", (i + 1) * 10 ** 11, t + i * 400, 100 + i, 0, f"s{i}")
                for i in range(1, 40)]
        out, _ = self.convert([create_row(t, 99, 0, "z")], [rows])
        market = Market()
        for r in out:
            ev = row_to_event(r)
            st = market.apply(ev, r["rx"])
            if ev.kind == "trade":
                want = _price(ev.reserve_quote, ev.reserve_base)
                self.assertAlmostEqual(st.price / want, 1.0, places=12)
        check = bf.check_tape(bf.tape_path(self.dir / "out", "slinky21", self.day))
        self.assertEqual(check["rows_checked"], 39)
        self.assertLess(check["max_rel_price_err"], 1e-12)

    def test_non_sol_rows_without_quote_fields_are_dropped(self):
        t = ms(2026, 8, 20, 12)
        c = Curve()
        good = c.trade("buy", 10 ** 12, t, 100, 0, "a")
        bad = dict(good, signature="b", slot=101, virtual_sol_reserves=0, real_sol_reserves=0, sol_amount=0)
        out, man = self.convert([create_row(t, 99, 0, "z")], [[good, bad]])
        self.assertEqual([r["sig"] for r in out if r["k"] == "trade"], ["a"])
        self.assertEqual(man["dropped"]["non_sol_no_quote_fields"], 1)


class JocryCleanTest(unittest.TestCase):
    def frame(self, rows):
        return pd.DataFrame(rows, columns=bf.JOCRY_TRADE_COLS + ["mayhem"])

    def row(self, i, buy, sol, tok, vtok, vsol, price):
        return [i, MINT, f"sig{i}", 0, buy, sol, tok, "w", vtok, vsol, price, False]

    def test_inconsistent_rows_are_rebuilt_repaired_or_dropped(self):
        vb = bf.PUMP_V_TOKENS - 10 ** 13               # after buying 10M tokens
        vq = K / vb
        px = vq / vb / 1000                            # SOL per whole token
        fill_sol = (vq - K / (vb + 10 ** 12)) / 1e9    # a 1M-token buy into that state
        rows = [
            self.row(1, True, fill_sol, 1e6, vb, vq, px),             # on the curve
            self.row(2, True, fill_sol, 1e6, vb * 1.3, vq, px),       # reserves off, price ok
            self.row(3, True, fill_sol, 1e6, None, None, px * 40),    # garbage price, no state
            self.row(4, True, None, 1e6, vb, vq, px),                  # sol missing
            self.row(5, True, fill_sol, None, vb, vq, px),             # no tokens
            self.row(6, False, fill_sol * 50, 1e6, vb, vq, px),        # sol 50x off the curve
        ]
        out, drops, fixes = bf.jocry_clean(self.frame(rows))
        self.assertEqual(sorted(out["id"]), [1, 2, 4, 6])
        self.assertEqual(drops, {"no_token_amount": 1, "no_consistent_curve_state": 1})
        self.assertEqual(fixes["curve_rebuilt"], 1)
        self.assertEqual(fixes["q_from_curve"], 2)
        r2 = out[out["id"] == 2].iloc[0]
        self.assertAlmostEqual(float(r2["vq"]) * float(r2["vb"]) / K, 1, places=6)
        self.assertAlmostEqual(_price(r2["vq"], r2["vb"]) / px, 1, places=6)
        r4 = out[out["id"] == 4].iloc[0]
        self.assertAlmostEqual(r4["q"] / (fill_sol * 1e9), 1, places=4)
        self.assertEqual(int(out[out["id"] == 1].iloc[0]["q"]), round(fill_sol * 1e9))


class JocryDayTest(TmpDir):
    def test_day_tape_from_spill_tokens_and_migrations(self):
        base = self.dir / "jocry"
        day = date(2026, 6, 20)
        t = ms(2026, 6, 20, 15)
        tz = pa.timestamp("us", tz="UTC")
        pq.write_table(pa.table({
            "mint": [MINT], "detected_at": pa.array([t * 1000], pa.int64()).cast(tz),
            "name": ["Coin"], "symbol": ["C"], "is_mayhem_mode": [False], "creator": ["dev"],
            "bonding_curve_key": ["curve"]}), self.dir / "tokens.parquet")
        pq.write_table(pa.table({
            "mint": [MINT, MINT], "migrated_at": pa.array([(t + 9000) * 1000, (t + 9500) * 1000], pa.int64()).cast(tz),
            "pool_address": ["synthetic_graduation_queue", "PoolX"]}), self.dir / "migrations.parquet")
        c = Curve()
        trades = []
        for i, (ix, tok) in enumerate([("buy", 10 ** 12), ("buy", 2 * 10 ** 12), ("sell", 10 ** 12)]):
            r = c.trade(ix, tok, t + 1000 * (i + 1), 0, 0, f"s{i}")
            trades.append({"id": i, "mint": MINT, "tx_signature": f"s{i}",
                           "event_time": pa.scalar((t + 1000 * (i + 1)) * 1000, pa.int64()).cast(
                               pa.timestamp("us", tz="+01:00")).as_py(),
                           "is_buy": ix == "buy", "sol_amount": r["sol_amount"] / 1e9,
                           "token_amount": tok / 1e6, "user_wallet": "w",
                           "v_tokens_bonding_curve": float(r["virtual_token_reserves"]),
                           "v_sol_bonding_curve": float(r["virtual_sol_reserves"]),
                           "price_sol": r["virtual_sol_reserves"] / r["virtual_token_reserves"] / 1000})
        trades.append(dict(trades[1]))                                 # duplicate
        (base / "trades").mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(trades[::-1]), base / "trades" / "trades-00000.parquet")
        for name in ("tokens", "migrations"):
            (self.dir / f"{name}.parquet").replace(base / f"{name}.parquet")
        spill = self.dir / "spill"
        counts = bf.jocry_spill(base, spill)
        self.assertEqual(counts, {20260620: 4})
        meta = bf.JocryMeta(base)
        man = bf.convert_jocry_day(day, meta, spill, self.dir / "out")
        out = read_rows(bf.tape_path(self.dir / "out", "jocry", day))
        self.assertEqual([r["k"] for r in out], ["create", "trade", "trade", "trade", "migrate", "migrate", "pool"])
        self.assertEqual([r.get("side") for r in out[1:4]], ["buy", "buy", "sell"])
        self.assertEqual(out[1]["rx"], t + 1000 + 1400)
        self.assertEqual(man["dropped"], {"duplicate_trade": 1, "pool_row_sentinel_address": 1})
        self.assertEqual(out[0]["x"]["supply"], 1_000_000_000)
        self.assertEqual(out[1]["fee"], 125)
        self.assertEqual(bf.check_tape(bf.tape_path(self.dir / "out", "jocry", day))["max_rel_price_err"], 0.0)


class OrderTxTradesTest(unittest.TestCase):
    def test_unchainable_group_keeps_original_order(self):
        group = [(0, "buy", 5, 100), (1, "buy", 7, 300)]
        self.assertEqual(bf.order_tx_trades(group), group)


if __name__ == "__main__":
    unittest.main()


class HistRunTest(TmpDir):
    def test_summary_totals_and_median_vs_base_random(self):
        from gemtracker.histrun import summarize
        rows = [{"algo": a, "return": r, "pnl_usd": r * 100, "trips": 2, "win_rate": 0.5,
                 "fees_sol": 0.01, "max_drawdown": 0.1}
                for a, rets in {"base_random": [-0.1, 0.0, 0.1], "x": [0.2, 0.3, -0.5]}.items()
                for r in rets]
        s = summarize(rows)
        self.assertAlmostEqual(s["x"]["pnl_usd_sum"], 0.0)
        self.assertEqual(s["x"]["median_day"], 0.2)
        self.assertEqual(s["x"]["median_vs_base_random"], 0.2)
        self.assertAlmostEqual(s["x"]["compounded"], round(1.2 * 1.3 * 0.5 - 1, 4))
        self.assertEqual(s["base_random"]["trips"], 6)

    def test_refuses_the_holdout(self):
        from gemtracker import histrun
        with self.assertRaises(SystemExit):
            histrun.main(["--root", str(bf.HOLDOUT_ROOT / "slinky21"), "--out", str(self.dir)])

    def test_run_day_on_a_small_tape(self):
        from gemtracker.histrun import run_day
        t = ms(2026, 8, 20, 12)
        c = Curve()
        rows = [c.trade("buy" if i % 4 else "sell", 3 * 10 ** 12, t + i * 700, 100 + 2 * i, 0, f"s{i}")
                for i in range(1, 200)]
        base = self.dir / "src"
        write_parquet(base / "p" / "a" / "create" / "c1.parquet", [create_row(t, 99, 0, "z")])
        write_parquet(base / "p" / "a" / "trade" / "t1.parquet", rows, row_group_size=50)
        bf.convert_slinky_day(date(2026, 8, 20), bf.SlinkyIndex(base, stable_s=0), self.dir / "out")
        res = run_day(bf.tape_path(self.dir / "out", "slinky21", date(2026, 8, 20)), 150.0,
                      "base_random,base_hold60")
        self.assertEqual({r["algo"] for r in res}, {"base_random", "base_hold60"})
        for r in res:
            self.assertGreaterEqual(r["max_drawdown"], 0.0)
            self.assertEqual(r["errors"], 0)

    def test_skips_days_without_trades(self):
        from gemtracker import histrun
        root = self.dir / "hist"
        for day, kinds in (("20260712", {}), ("20260713", {"create": 1})):
            d = root / "jocry" / day
            d.mkdir(parents=True)
            (d / "day.jsonl.gz").write_bytes(gzip.compress(b""))
            (d / "manifest.json").write_text(json.dumps({"rows_by_kind": kinds}), encoding="utf-8")
        out = self.dir / "res"
        histrun.main(["--root", str(root), "--out", str(out), "--algos", "base_random",
                      "--sol-usd", "150"])
        self.assertEqual(json.loads((out / "summary.json").read_text("utf-8"))["days"], 0)
        self.assertEqual(sorted(json.loads((out / "summary.json").read_text("utf-8"))["skipped"]),
                         ["jocry 2026-07-12", "jocry 2026-07-13"])
