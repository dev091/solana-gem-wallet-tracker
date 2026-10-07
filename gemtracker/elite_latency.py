"""Latency decay of each elite's round trips, from the local history (DuckDB, one pass).

    python -m gemtracker.elite_latency [--names Cented,Cupsey] [--out DIR]

For every closed round trip in data/history/elite_trades/trips_<Name>.parquet the pump-curve
price on the same mint is read from mint_trades.parquet:

  * `late[d]`   buy d seconds after his entry (last trade at or before entry_t + d; d = 0 is
                the last trade in his entry second, i.e. right behind him), sell at his exit
                price (trips.exit_mcap). Multiple = exit / late entry, net of a fixed
                round-trip fee (FEE_RT). This is the "copy his mint selection at latency d" test.
  * `path[h]`   from the LATE_REF-second-late entry, the price h seconds later (time-exit
                instead of his exit): which of his mints still move after we could be in.

Only the dev span is read (the trips files were built without the holdout; the module
refuses any trip at or after HOLDOUT_EPOCH as a guard). Output: latency_<Name>.json with
quantiles, win rate and mean net return per delay, nothing per trip.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .elite_trades import HOLDOUT_EPOCH, OUT

DELAYS = (0, 1, 3, 4, 10, 30)          # seconds after his entry (3 ~ our 2.5 s + feed lag)
HOLDS = (10, 30, 60, 120, 300)         # seconds after the late entry
LATE_REF = 3
FEE_RT = 0.025                         # 1.25 % venue fee each way, tx fees excluded
NAMES = ("Cented", "Cupsey", "Theo", "Trunoest", "Cooker", "Mr_Frog", "Cap", "Trenchman",
         "Smokez", "Decu")


def summarize(mults: list[float], fee_rt: float = FEE_RT) -> dict:
    """Quantiles, win rate and mean net return of price multiples after a fixed round-trip fee."""
    xs = sorted(m for m in mults if m is not None and m > 0)
    if not xs:
        return {"n": 0}

    def q(p: float) -> float:
        return round(xs[min(len(xs) - 1, int(p * len(xs)))], 4)

    net = [m * (1 - fee_rt) - 1 for m in xs]
    return {"n": len(xs), "p10": q(0.1), "p25": q(0.25), "p50": q(0.5), "p75": q(0.75),
            "p90": q(0.9), "win_rate": round(sum(1 for r in net if r > 0) / len(net), 3),
            "mean_net": round(sum(net) / len(net), 4)}


def _query(con, trips: Path, trades: Path) -> dict:
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE trips AS
        SELECT mint, entry_t, exit_t, mcap, mcap_post, exit_mcap, mult, hold, win, sol_in
        FROM read_parquet('{trips.as_posix()}')
        WHERE exit_mcap > 0 AND mcap_post > 0 AND exit_t >= entry_t AND entry_t < {HOLDOUT_EPOCH}
    """)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE px AS
        SELECT p.mint, p.t, p.slot, p.tx_index,
               p.virtual_sol_reserves * 1e6 / p.virtual_token_reserves AS mcap
        FROM read_parquet('{trades.as_posix()}') p
        SEMI JOIN trips USING (mint)
        WHERE p.virtual_token_reserves > 0
    """)
    out = {"n_trips": con.execute("SELECT count(*) FROM trips").fetchone()[0],
           "his": summarize([r[0] for r in con.execute(
               "SELECT exit_mcap / mcap_post FROM trips").fetchall()]),
           "his_realised": summarize([r[0] for r in con.execute(
               "SELECT mult FROM trips").fetchall()], fee_rt=0.0),
           "late": {}, "path": {}}
    for d in DELAYS:
        rows = con.execute(f"""
            SELECT t.exit_mcap / p.mcap
            FROM trips t ASOF JOIN px p ON p.mint = t.mint AND p.t <= t.entry_t + {d}
        """).fetchall()
        out["late"][str(d)] = summarize([r[0] for r in rows])
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE late AS
        SELECT t.mint, t.entry_t + {LATE_REF} AS t0, p.mcap AS m0
        FROM trips t ASOF JOIN px p ON p.mint = t.mint AND p.t <= t.entry_t + {LATE_REF}
    """)
    for h in HOLDS:
        rows = con.execute(f"""
            SELECT p.mcap / l.m0
            FROM late l ASOF JOIN px p ON p.mint = l.mint AND p.t <= l.t0 + {h}
        """).fetchall()
        out["path"][str(h)] = summarize([r[0] for r in rows])
    rows = con.execute(f"""
        SELECT max(p.mcap) / any_value(l.m0)
        FROM late l JOIN px p ON p.mint = l.mint AND p.t > l.t0 AND p.t <= l.t0 + 60
        GROUP BY l.mint, l.t0
    """).fetchall()
    out["path"]["peak_60"] = summarize([r[0] for r in rows], fee_rt=0.0)
    return out


def measure(name: str, root: Path = OUT) -> dict:
    import duckdb
    trips = root / f"trips_{name}.parquet"
    trades = root / "mint_trades.parquet"
    con = duckdb.connect()
    try:
        con.execute("SET threads TO 2")
        return {"name": name, **_query(con, trips, trades)}
    finally:
        con.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="latency decay of elite round trips")
    ap.add_argument("--names", default=",".join(NAMES))
    ap.add_argument("--root", default=str(OUT))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.names.split(","):
        name = name.strip()
        r = measure(name, root)
        (out / f"latency_{name}.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
        late = {d: (v.get("p50"), v.get("win_rate")) for d, v in r["late"].items()}
        print(f"{name:10s} n={r['n_trips']} his p50 {r['his'].get('p50')} late(p50,WR) {late}",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
