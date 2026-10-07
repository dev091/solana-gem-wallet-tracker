"""Run every paper algo over converted history tapes, one ET day at a time.

    python -m gemtracker.histrun --source slinky21 --from 2026-08-08 --to 2026-09-04

Each day starts fresh at SimConfig.start_usd with the live SimConfig (fees, latency) and the
algos exactly as they are. Results go to data/paper/hist_dev/: one row per (day, algo) in
`days.csv` / `days.jsonl`, and per-algo totals in `summary.json`. Only the dev tapes
(data/tapes/hist) are accepted; the holdout is refused.

SOL/USD is fixed per run (default: the live recorder's last value) and only sets the
starting balance in SOL; returns are in SOL terms.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from dataclasses import asdict
import time
from datetime import date
from pathlib import Path

from .backfill import DEV_ROOT, HOLDOUT_ROOT, day_tapes, iter_day
from .config import DATA_DIR
from .papersim import SimConfig
from .replay import replay

OUT_DIR = DATA_DIR / "paper" / "hist_dev"
SAMPLE_MS = 60_000
COLUMNS = ["day", "source", "algo", "return", "pnl_usd", "trips", "win_rate", "fees_sol",
           "max_drawdown", "fills", "rejects", "open_at_end", "errors"]


class DayProbe:
    """Once a minute: each book's equity (for max drawdown), and prune the market as live does."""

    def __init__(self):
        self.next = None
        self.peak, self.mdd = {}, {}

    def sample(self, sim, market):
        for name, book in sim.books.items():
            eq = book.equity_sol(market)
            peak = max(self.peak.get(name, book.start_sol), eq)
            self.peak[name] = peak
            self.mdd[name] = max(self.mdd.get(name, 0.0), 1 - eq / peak if peak > 0 else 0.0)

    def __call__(self, sim, market, now_ms):
        if self.next is None:
            self.next = now_ms
        if now_ms < self.next:
            return
        self.next = now_ms + SAMPLE_MS
        self.sample(sim, market)
        held = {m for b in sim.books.values() for m in b.positions}
        held |= {p.intent.mint for b in sim.books.values() for p in b.pending}
        market.prune(now_ms, held)


def run_day(path: Path, sol_usd: float, algos: str = "all", cfg: SimConfig | None = None,
            out_dir: Path | None = None) -> list[dict]:
    from . import elite
    from .live import load_algos
    cfg = cfg or SimConfig()
    probe = DayProbe()
    sim, market = replay(load_algos(algos), cfg, iter_day(path), sol_usd,
                         {e.wallet: e.name for e in elite.ELITES}, out_dir, probe=probe)
    probe.sample(sim, market)
    rows = []
    for s in sim.summary(market):
        book = sim.books[s["algo"]]
        rows.append({"algo": s["algo"], "return": s["return"],
                     "pnl_usd": round(s["equity_usd"] - cfg.start_usd, 2), "trips": s["closed"],
                     "win_rate": s["win_rate"],
                     "fees_sol": round(s["venue_fees_sol"] + s["tx_fees_sol"], 4),
                     "max_drawdown": round(probe.mdd.get(s["algo"], 0.0), 4),
                     "fills": s["fills"], "rejects": s["rejects"], "open_at_end": s["open"],
                     "errors": getattr(book, "errors", 0)})
    return rows


def summarize(rows: list[dict]) -> dict:
    """Per algo over all days: summed daily PnL, compounded and median daily return, and
    each algo's median day minus base_random's median day."""
    by = {}
    for r in rows:
        by.setdefault(r["algo"], []).append(r)
    out = {}
    for algo, rs in by.items():
        rets = [r["return"] for r in rs]
        comp = 1.0
        for x in rets:
            comp *= 1 + x
        trips = sum(r["trips"] for r in rs)
        wins = sum((r["win_rate"] or 0) * r["trips"] for r in rs)
        out[algo] = {"days": len(rs), "pnl_usd_sum": round(sum(r["pnl_usd"] for r in rs), 2),
                     "mean_day": round(statistics.mean(rets), 4),
                     "median_day": round(statistics.median(rets), 4),
                     "compounded": round(comp - 1, 4),
                     "up_days": sum(1 for x in rets if x > 0), "trips": trips,
                     "win_rate": round(wins / trips, 3) if trips else None,
                     "fees_sol": round(sum(r["fees_sol"] for r in rs), 4),
                     "worst_day": round(min(rets), 4),
                     "max_drawdown": round(max(r["max_drawdown"] for r in rs), 4)}
    base = out.get("base_random", {}).get("median_day")
    for v in out.values():
        v["median_vs_base_random"] = round(v["median_day"] - base, 4) if base is not None else None
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["pnl_usd_sum"]))


def last_sol_usd(default: float = 150.0) -> float:
    try:
        st = json.loads((DATA_DIR / "paper" / "recorder" / "status.json").read_text("utf-8"))
        return float(st["sol_usd"])
    except (OSError, ValueError, KeyError, TypeError):
        return default


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="replay all paper algos over history day tapes")
    ap.add_argument("--source", action="append", choices=["slinky21", "jocry"])
    ap.add_argument("--from", dest="start", default="")
    ap.add_argument("--to", dest="end", default="")
    ap.add_argument("--root", default=str(DEV_ROOT))
    ap.add_argument("--algos", default="all")
    ap.add_argument("--sol-usd", type=float, default=0.0)
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if root == HOLDOUT_ROOT.resolve() or HOLDOUT_ROOT.resolve() in root.parents:
        raise SystemExit("refusing to replay the holdout")
    sol_usd = args.sol_usd or last_sol_usd()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    a = date.fromisoformat(args.start) if args.start else None
    b = date.fromisoformat(args.end) if args.end else None
    jl = out / "days.jsonl"
    done = set()
    rows = []
    if jl.exists():  # resume: keep finished days
        for line in jl.read_text("utf-8").splitlines():
            r = json.loads(line)
            rows.append(r)
            done.add((r["source"], r["day"]))
    for source in args.source or ["jocry", "slinky21"]:
        for day, path in day_tapes(root, source, a, b):
            if (source, day.isoformat()) in done:
                continue
            t = time.time()
            day_rows = [dict(day=day.isoformat(), source=source, **r)
                        for r in run_day(path, sol_usd, args.algos)]
            with open(jl, "a", encoding="utf-8") as fh:
                for r in day_rows:
                    fh.write(json.dumps(r) + "\n")
            rows += day_rows
            best = max(day_rows, key=lambda r: r["return"])
            print(f"{source} {day} {time.time() - t:.0f}s best {best['algo']} {best['return']:+.3f}",
                  flush=True)
    rows.sort(key=lambda r: (r["day"], r["algo"]))
    with open(out / "days.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, COLUMNS)
        w.writeheader()
        w.writerows(rows)
    summary = {"sol_usd": sol_usd, "sim": asdict(SimConfig()),
               "days": len({(r["source"], r["day"]) for r in rows}),
               "note": "each day from a fresh start_usd; tapes have no post-migration PumpSwap "
                       "trades", "algos": summarize(rows)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for algo, v in summary["algos"].items():
        print(f"{algo:16s} pnl ${v['pnl_usd_sum']:>9.2f} median {v['median_day']:+.4f} "
              f"vs base_random {v['median_vs_base_random']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
