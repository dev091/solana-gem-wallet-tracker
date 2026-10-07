"""Pull every elite-wallet trade out of the free local datasets in one DuckDB pass.

Sources (already on D:): Kaggle pump-or-dump daily swaps (signing_wallet) and Slinky21
pump.fun trade events (trade_user). Rows on or after the holdout start (2026-09-05 ET) are
dropped before anything is written, so the holdout is never inspected.

    python -m gemtracker.elite_trades
"""
from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import DATA_DIR
from .elite import ELITES

HIST = DATA_DIR / "history"
OUT = HIST / "elite_trades"
HOLDOUT_EPOCH = int(datetime(2026, 9, 5, tzinfo=ZoneInfo("America/New_York")).timestamp())


def main() -> int:
    import duckdb
    OUT.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect()
    c.execute("SET threads TO 4")
    c.execute("CREATE TABLE w AS SELECT * FROM (VALUES " +
              ",".join(f"('{e.wallet}','{e.name}')" for e in ELITES) + ") t(wallet, name)")
    kg = (HIST / "kaggle" / "memecoins-pump-or-dump").as_posix()
    hf = (HIST / "hf" / "Slinky21").as_posix()
    jobs = {
        "kaggle": f"""SELECT w.name, epoch(block_time)::BIGINT AS t, regexp_extract(filename, '_(pumpfun|pumpswap)_', 1) AS venue, s.*
                      FROM read_parquet('{kg}/day_*_all_swaps.parquet', union_by_name=true, filename=true) s
                      JOIN w ON s.signing_wallet = w.wallet
                      WHERE epoch(block_time) < {HOLDOUT_EPOCH}""",
        "slinky": f"""SELECT w.name, epoch(block_time)::BIGINT AS t, s.*
                      FROM read_parquet('{hf}/**/trade/*.parquet', union_by_name=true) s
                      JOIN w ON s.trade_user = w.wallet
                      WHERE epoch(block_time) < {HOLDOUT_EPOCH}""",
    }
    for name, sql in jobs.items():
        t0 = time.time()
        out = (OUT / f"{name}.parquet").as_posix()
        c.execute(f"COPY ({sql}) TO '{out}' (FORMAT parquet)")
        rows = c.execute(f"SELECT name, count(*), to_timestamp(min(t)), to_timestamp(max(t)) FROM '{out}' GROUP BY 1 ORDER BY 2 DESC").fetchall()
        print(f"{name}: {time.time() - t0:.0f}s")
        for r in rows:
            print("  ", r[0], r[1], r[2], r[3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
