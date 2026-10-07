"""Latency-decay and copy-follow screens on a tiny synthetic history (DuckDB, no tapes)."""
import json
from pathlib import Path

import pytest

duckdb = pytest.importorskip("duckdb")

from gemtracker import elite_copy_screen as ecs  # noqa: E402
from gemtracker import elite_latency as el  # noqa: E402

T0 = 1_786_000_000  # well before HOLDOUT_EPOCH


def _reserves(mcap: float):
    """virtual reserves giving mcap = vsr * 1e6 / vtr."""
    vtr = 1_000_000_000_000
    return mcap * vtr / 1e6, vtr


@pytest.fixture
def hist(tmp_path: Path) -> Path:
    """Two trips on FIT days: mint A doubles after his entry, mint B halves."""
    con = duckdb.connect()
    con.execute("CREATE TABLE px (mint VARCHAR, t BIGINT, slot BIGINT, tx_index BIGINT, "
                "virtual_sol_reserves DOUBLE, virtual_token_reserves DOUBLE)")
    path = {"A": [(0, 40.0), (1, 42.0), (3, 44.0), (30, 80.0), (60, 85.0), (100, 90.0)],
            "B": [(0, 40.0), (1, 40.0), (3, 38.0), (30, 24.0), (60, 20.0), (100, 20.0)]}
    for mint, pts in path.items():
        for i, (dt, m) in enumerate(pts):
            vsr, vtr = _reserves(m)
            con.execute("INSERT INTO px VALUES (?,?,?,?,?,?)", [mint, T0 + dt, i, 0, vsr, vtr])
    con.execute(f"COPY px TO '{(tmp_path / 'mint_trades.parquet').as_posix()}' (FORMAT PARQUET)")
    con.execute("CREATE TABLE trips (mint VARCHAR, entry_t BIGINT, exit_t BIGINT, mcap DOUBLE, "
                "mcap_post DOUBLE, exit_mcap DOUBLE, mult DOUBLE, hold DOUBLE, win BOOLEAN, "
                "sol_in DOUBLE, day VARCHAR)")
    con.execute("INSERT INTO trips VALUES ('A', ?, ?, 40, 40, 85, 2.1, 60, true, 1, '2026-08-10')",
                [T0, T0 + 60])
    con.execute("INSERT INTO trips VALUES ('B', ?, ?, 40, 40, 20, 0.5, 60, false, 1, '2026-08-11')",
                [T0, T0 + 60])
    con.execute(f"COPY trips TO '{(tmp_path / 'trips_X.parquet').as_posix()}' (FORMAT PARQUET)")
    con.close()
    return tmp_path


def test_summarize_fee_and_win_rate():
    s = el.summarize([2.0, 0.5, 1.0], fee_rt=0.025)
    assert s["n"] == 3 and s["win_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert s["mean_net"] == pytest.approx((2 + 0.5 + 1) / 3 * 0.975 - 1, abs=1e-4)
    assert el.summarize([]) == {"n": 0}


def test_latency_decay_uses_asof_price(hist):
    r = el.measure("X", root=hist)
    assert r["n_trips"] == 2
    # his exit / his fill: A 85/40, B 20/40 -> median of the two sorted values at index 1
    assert r["his"]["p50"] == pytest.approx(85 / 40, abs=1e-3)
    # 3 s late: A bought at 44 (exit 85), B at 38 (exit 20)
    late3 = r["late"]["3"]
    assert late3["n"] == 2 and late3["p50"] == pytest.approx(85 / 44, abs=1e-3)
    assert late3["win_rate"] == 0.5
    # 30 s path from the 3 s entry: A 80/44, B 24/38
    assert r["path"]["30"]["p50"] == pytest.approx(80 / 44, abs=1e-3)
    assert r["path"]["peak_60"]["n"] == 2


def test_copy_screen_grid_counted_and_fees_per_fill(hist):
    r = ecs.screen("X", "fit", root=hist)
    assert r["trials"] == len(ecs.CHASE) * len(ecs.HOLD) * len(ecs.STOP) == 48
    assert r["ndays"] == 2
    plain = r["plain_copy"]
    assert plain["n"] == 2
    # exit 3 s after his exit (t+63 -> last trade at t+60): A 85/44, B 20/38
    exp = (ecs.trade_net(44, 85, 1.0) + ecs.trade_net(38, 20, 1.0)) / 2
    assert plain["net_1sol"] == pytest.approx(exp, abs=1e-3)
    assert plain["net_5usd"] < plain["net_1sol"]          # tx fee bites the small clip
    # stop 0.70 catches B (min 24 <= 0.7*38) and fills 2 % under the level
    stopped = next(g for g in r["grid"] if g["chase"] is None and g["hold"] is None
                   and g["stop"] == 0.70)
    exp_b = ecs.trade_net(38, 0.7 * 38 * 0.98, 1.0)
    assert stopped["net_1sol"] == pytest.approx((ecs.trade_net(44, 85, 1.0) + exp_b) / 2, abs=1e-3)
    # chase 1.03 skips both (44/40 and 38/40 are outside +3 % / below); 1.10 keeps A only
    assert all(not (g["chase"] == 1.03) for g in r["grid"]) or \
        all(g["n"] == 1 for g in r["grid"] if g["chase"] == 1.03)
    assert all(g["n"] == 2 for g in r["grid"] if g["chase"] == 1.10)


def test_val_days_filter_excludes_fit_trips(hist):
    r = ecs.screen("X", "val", root=hist)
    assert r["ndays"] == 0 and r["best"] is None


def test_main_writes_json(hist, capsys):
    assert ecs.main(["--names", "X", "--root", str(hist), "--out", str(hist)]) == 0
    assert json.loads((hist / "copyscreen_fit_X.json").read_text())["trials"] == 48
    assert el.main(["--names", "X", "--root", str(hist), "--out", str(hist)]) == 0
    assert (hist / "latency_X.json").exists()
