"""Head-to-head scoreboard: our paper algos vs the real elites, by US Eastern day and rolling 30 days.

Elites: their closed round trips on the venues we decode (data/profiles/<name>.trips.jsonl from the
profiler), PnL = SOL out - SOL in, before their network fees. Trades on other DEXes are invisible to
the free feed, so this is their visible PnL only.
Algos: realized PnL from the paper fill ledgers (data/paper/<run>/<algo>.jsonl), all fees included;
rejected orders cost their network fee.

The fair comparison is return per SOL deployed: the elites trade far more capital than $100.
USD PnL is shown next to the leaderboard targets.

    python -m gemtracker.scoreboard --run live [--days 30] [--sol-usd 116]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .config import DATA_DIR

PROFILE_DIR = DATA_DIR / "profiles"
PAPER_DIR = DATA_DIR / "paper"
TARGET_DAY_USD = 1_500          # Rahul's daily target per algo (from 2026-10-07 7:25 PM ET)
DECU_BEST_MONTH_USD = 277_000   # Decu's best month (Rahul, 2026-10-07)
ELITE_MONTH_USD = 1_000_000     # top elite tier per month
START_USD = 100.0


def _nth_sunday(year: int, month: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def et_day(ms: int) -> date:
    """US Eastern calendar day of a UTC epoch-ms time (DST: 2nd Sunday March to 1st Sunday November)."""
    utc = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    y = utc.year
    start = datetime.combine(_nth_sunday(y, 3, 2), datetime.min.time(), timezone.utc) + timedelta(hours=7)
    end = datetime.combine(_nth_sunday(y, 11, 1), datetime.min.time(), timezone.utc) + timedelta(hours=6)
    offset = 4 if start <= utc < end else 5
    return (utc - timedelta(hours=offset)).date()


def _row(entity: str, kind: str) -> dict:
    return {"entity": entity, "kind": kind, "pnl_sol": 0.0, "pnl_usd": 0.0, "deployed_sol": 0.0,
            "trips": 0, "wins": 0}


def elite_days(profile_dir: Path, sol_usd: float) -> dict:
    """{(name, et_day): row} from closed elite round trips, booked on the day they closed."""
    out = {}
    for path in sorted(profile_dir.glob("*.trips.jsonl")):
        name = path.name[: -len(".trips.jsonl")]
        for line in path.read_text(encoding="utf-8").splitlines():
            t = json.loads(line)
            day = et_day(t["open_rx"] + int(t.get("hold_s", 0) * 1000))
            r = out.setdefault((name, day), _row(name, "elite"))
            pnl = t["sol_out"] - t["sol_in"]
            r["pnl_sol"] += pnl
            r["pnl_usd"] += pnl * sol_usd
            r["deployed_sol"] += t["sol_in"]
            r["trips"] += 1
            r["wins"] += pnl > 0
    return out


def algo_days(run_dir: Path) -> dict:
    """{(algo, et_day): row} from paper fill ledgers."""
    out = {}
    skip = {"summary.jsonl", "status.json", "config.json"}
    for path in sorted(run_dir.glob("*.jsonl")):
        if path.name in skip:
            continue
        algo = path.stem
        for line in path.read_text(encoding="utf-8").splitlines():
            add_fill(out, algo, json.loads(line))
    return out


def add_fill(out: dict, algo: str, f: dict) -> None:
    """Book one ledger line into {(algo, et_day): row}."""
    r = out.setdefault((algo, et_day(f["arrival_ms"])), _row(algo, "algo"))
    usd = f.get("sol_usd") or 0.0
    if f["status"] != "filled":
        r["pnl_sol"] -= f.get("tx_fee_sol", 0.0)
        r["pnl_usd"] -= f.get("tx_fee_sol", 0.0) * usd
    elif f["side"] == "buy":
        r["deployed_sol"] += f["sol"]
    else:
        r["pnl_sol"] += f["pnl_sol"]
        r["pnl_usd"] += f["pnl_sol"] * usd
        r["trips"] += 1
        r["wins"] += f["pnl_sol"] > 0


def board(rows: dict, days: int, today: date | None = None) -> list[dict]:
    """Per entity: last day and rolling `days` totals, gaps to the targets, ranked by return per SOL."""
    today = today or max((d for _, d in rows), default=date.today())
    first = today - timedelta(days=days - 1)
    agg = defaultdict(lambda: None)
    for (name, day), r in rows.items():
        if not first <= day <= today:
            continue
        a = agg[name] or {**_row(name, r["kind"]), "today_usd": 0.0, "active_days": 0}
        for k in ("pnl_sol", "pnl_usd", "deployed_sol", "trips", "wins"):
            a[k] += r[k]
        a["active_days"] += 1
        if day == today:
            a["today_usd"] = r["pnl_usd"]
        agg[name] = a
    out = []
    for a in agg.values():
        ret = a["pnl_sol"] / a["deployed_sol"] if a["deployed_sol"] else None
        out.append({"entity": a["entity"], "kind": a["kind"],
                    "today_usd": round(a["today_usd"], 2), "window_usd": round(a["pnl_usd"], 2),
                    "window_sol": round(a["pnl_sol"], 4), "deployed_sol": round(a["deployed_sol"], 4),
                    "return_per_sol": round(ret, 4) if ret is not None else None,
                    "trips": a["trips"], "win_rate": round(a["wins"] / a["trips"], 3) if a["trips"] else None,
                    "active_days": a["active_days"],
                    "on_start": round(a["pnl_usd"] / START_USD, 3) if a["kind"] == "algo" else None,
                    "gap_today_usd": round(TARGET_DAY_USD - a["today_usd"], 2),
                    "pct_of_decu_best_month": round(a["pnl_usd"] / DECU_BEST_MONTH_USD, 4),
                    "pct_of_elite_month": round(a["pnl_usd"] / ELITE_MONTH_USD, 4)})
    return sorted(out, key=lambda r: -(r["return_per_sol"] if r["return_per_sol"] is not None else -9e9))


def _sol_usd_default() -> float:
    try:
        return float(json.loads((PAPER_DIR / "recorder" / "status.json").read_text())["sol_usd"])
    except (OSError, KeyError, ValueError):
        raise SystemExit("pass --sol-usd (no recorder status.json to read it from)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="our algos vs the elites, per ET day and rolling window")
    ap.add_argument("--run", default="live", help="paper run directory under data/paper")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--sol-usd", type=float, default=None, help="SOL/USD for elite PnL (default: recorder)")
    args = ap.parse_args(argv)
    rows = elite_days(PROFILE_DIR, args.sol_usd or _sol_usd_default())
    run_dir = PAPER_DIR / args.run
    if run_dir.is_dir():
        rows |= algo_days(run_dir)
    result = board(rows, args.days)
    print(f"{'entity':16} {'kind':5} {'ret/SOL':>8} {'today $':>10} {f'{args.days}d $':>12} {'win':>6} {'trips':>6}")
    for r in result:
        ret = f"{r['return_per_sol']:+.1%}" if r["return_per_sol"] is not None else "-"
        win = f"{r['win_rate']:.0%}" if r["win_rate"] is not None else "-"
        print(f"{r['entity'][:16]:16} {r['kind']:5} {ret:>8} {r['today_usd']:>10,.0f} {r['window_usd']:>12,.0f}"
              f" {win:>6} {r['trips']:>6}")
    out = run_dir if run_dir.is_dir() else PROFILE_DIR
    (out / "scoreboard.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
