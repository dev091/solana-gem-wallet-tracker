"""Vectorized copy-follow screen: what a latency-bound copier of each elite would have made.

    python -m gemtracker.elite_copy_screen [--names Cooker,Cap] [--days fit|val] [--out DIR]

One DuckDB pass per elite over trips_<Name>.parquet + mint_trades.parquet (no tape replay):

  entry  last pump-curve trade at or before his entry + LAT_S (our 2.5 s latency plus feed lag)
  exit   the earliest of: his exit + LAT_S (we see his sell on the tape, then react late),
         a time stop `hold` seconds after our entry, or a stop-loss `stop` (filled 2 % below
         the stop level); all prices by ASOF join on the trade stream.
  chase  the order is skipped when our entry price is more than `chase` x his fill price
         (the Buy max_slippage guard in the paper sim).
  fees   venue fee FEE_SIDE per side plus TX_SOL per fill, reported at two clip sizes
         ($5 clip on the $100 book and a 1 SOL clip) as separate net columns.

Grid = CHASE x HOLD x STOP; every point counts as a trial. `--days fit` uses the fixed FIT
span (<= 2026-08-24 ET), `--days val` the VALIDATION span (>= 2026-08-25); the trips files
never contain holdout days (built before HOLDOUT_EPOCH). Selection is on FIT only; the VAL
run reports the whole grid so the frozen FIT point can be read off once.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from .elite_trades import HOLDOUT_EPOCH, OUT

LAT_S = 3
FEE_SIDE = 0.0125
TX_SOL = 0.001
CLIPS = {"net_5usd": 0.033, "net_1sol": 1.0}
CHASE = (1.03, 1.10, 1.25, None)
HOLD = (30, 120, 600, None)
STOP = (None, 0.70, 0.85)
FIT_LAST_DAY, VAL_FIRST_DAY = "2026-08-24", "2026-08-25"
NAMES = ("Smokez", "Trenchman", "Mr_Frog", "Cooker", "Cap", "Cented", "Cupsey", "Theo",
         "Trunoest", "Decu")


def grid() -> list[tuple]:
    return list(itertools.product(CHASE, HOLD, STOP))


def trade_net(p_in: float, p_out: float, clip_sol: float) -> float:
    """Net return of one round trip after venue fees per side and the tx fee per fill."""
    return (p_out / p_in) * (1 - FEE_SIDE) ** 2 - 1 - 2 * TX_SOL / clip_sol


def _rows(con, trips: Path, trades: Path, day_filter: str) -> tuple[int, dict]:
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE trips AS
        SELECT mint, entry_t, exit_t, mcap_post, day
        FROM read_parquet('{trips.as_posix()}')
        WHERE exit_mcap > 0 AND mcap_post > 0 AND exit_t >= entry_t
          AND entry_t < {HOLDOUT_EPOCH} AND {day_filter}
    """)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE px AS
        SELECT p.mint, p.t, p.virtual_sol_reserves * 1e6 / p.virtual_token_reserves AS m
        FROM read_parquet('{trades.as_posix()}') p SEMI JOIN trips USING (mint)
        WHERE p.virtual_token_reserves > 0
    """)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE base AS
        SELECT t.*, t.entry_t + {LAT_S} AS t0, a.m AS p_in, b.m AS p_his
        FROM trips t
        ASOF JOIN px a ON a.mint = t.mint AND a.t <= t.entry_t + {LAT_S}
        ASOF JOIN px b ON b.mint = t.mint AND b.t <= t.exit_t + {LAT_S}
    """)
    ndays = con.execute("SELECT count(DISTINCT day) FROM trips").fetchone()[0]
    rows = {}
    for h in HOLD:
        hh = h if h is not None else 10 ** 9
        rows[h] = con.execute(f"""
            SELECT b.entry_t, b.exit_t, b.p_in, b.p_his, b.mcap_post, c.m AS p_h,
                   (SELECT min(m) FROM px p WHERE p.mint = b.mint AND p.t > b.t0
                      AND p.t <= least(b.t0 + {hh}, b.exit_t + {LAT_S})) AS mn
            FROM base b ASOF JOIN px c ON c.mint = b.mint AND c.t <= b.t0 + {hh}
        """).fetchall()
    return ndays, rows


def evaluate(ndays: int, rows: dict) -> list[dict]:
    out = []
    for chase, hold, stop in grid():
        nets = {k: [] for k in CLIPS}
        for entry_t, exit_t, p_in, p_his, mpost, p_h, mn in rows[hold]:
            if p_in is None or p_in <= 0 or (chase and p_in / mpost > chase):
                continue
            timed = hold is not None and exit_t + LAT_S > entry_t + LAT_S + hold
            p_out = p_h if timed else p_his
            if stop and mn is not None and mn <= stop * p_in:
                p_out = stop * p_in * 0.98
            for k, clip in CLIPS.items():
                nets[k].append(trade_net(p_in, p_out, clip))
        n = len(nets["net_1sol"])
        if not n:
            continue
        rec = {"chase": chase, "hold": hold, "stop": stop, "n": n,
               "per_day": round(n / max(ndays, 1), 2),
               "win_rate": round(sum(x > 0 for x in nets["net_1sol"]) / n, 3)}
        for k in CLIPS:
            rec[k] = round(sum(nets[k]) / n, 4)
        rec["sol_day_1sol"] = round(sum(nets["net_1sol"]) / max(ndays, 1), 3)
        out.append(rec)
    out.sort(key=lambda r: -r["net_1sol"])
    return out


def screen(name: str, days: str = "fit", root: Path = OUT) -> dict:
    import duckdb
    day_filter = (f"day <= '{FIT_LAST_DAY}'" if days == "fit" else f"day >= '{VAL_FIRST_DAY}'")
    con = duckdb.connect()
    try:
        con.execute("SET threads TO 3")
        ndays, rows = _rows(con, root / f"trips_{name}.parquet", root / "mint_trades.parquet",
                            day_filter)
    finally:
        con.close()
    res = evaluate(ndays, rows)
    plain = [r for r in res if r["chase"] is None and r["hold"] is None and r["stop"] is None]
    return {"name": name, "days": days, "ndays": ndays, "trials": len(grid()), "grid": res,
            "best": res[0] if res else None, "plain_copy": plain[0] if plain else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="vectorized copy-follow screen per elite")
    ap.add_argument("--names", default=",".join(NAMES))
    ap.add_argument("--days", choices=("fit", "val"), default="fit")
    ap.add_argument("--root", default=str(OUT))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.names.split(","):
        r = screen(name.strip(), args.days, Path(args.root))
        (out / f"copyscreen_{args.days}_{r['name']}.json").write_text(json.dumps(r, indent=1),
                                                                      encoding="utf-8")
        b, p = r["best"] or {}, r["plain_copy"] or {}
        print(f"{r['name']:10s} days={r['ndays']} trials={r['trials']} best "
              f"{(b.get('chase'), b.get('hold'), b.get('stop'))} net_1sol {b.get('net_1sol')} "
              f"WR {b.get('win_rate')} n/day {b.get('per_day')} | plain copy net_1sol "
              f"{p.get('net_1sol')} WR {p.get('win_rate')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
