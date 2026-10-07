"""Elite-trader dossiers built from the tape: every trade they made, with the coin's state
just before it (what they could see), and their round trips.

Data: decoded trades where the elite wallet is the trader (Pump.fun, PumpSwap, LaunchLab).
History through the RPC is not usable on free endpoints: ~300 spam transactions a second
mention each elite wallet, so 1000 signatures cover about 3 seconds.

    python -m gemtracker.profiler [--start 20261007/18] [--end ...]
Writes data/profiles/<name>.trades.jsonl, <name>.trips.jsonl and summary.json.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from . import elite
from .config import DATA_DIR
from .market import Market
from .replay import row_to_event
from .tape import TAPE_DIR, read_tape

PROFILE_DIR = DATA_DIR / "profiles"


def context(st, now_ms: int) -> dict:
    """The coin as it stood just before the trade (strictly earlier information)."""
    if st is None:
        return {"known": False}
    w10, w60 = st.window(now_ms, 10), st.window(now_ms, 60)
    return {"known": True, "venue": st.venue, "seen_create": st.seen_create,
            "age_s": round(st.age_s(now_ms), 1), "mcap_sol": round(st.mcap, 2),
            "ath_mcap_sol": round(st.ath_mcap, 2), "progress": round(st.progress, 4),
            "migrated": st.migrated, "mayhem": st.mayhem, "n_buys": st.n_buys, "n_sells": st.n_sells,
            "holders": st.holder_count(), "top10": round(st.top_holder_share(), 4),
            "dev_sold_frac": round(st.dev_sold / st.dev_bought, 3) if st.dev_bought else None,
            "w10": {k: round(v, 4) for k, v in w10.items()},
            "w60": {k: round(v, 4) for k, v in w60.items()},
            "elite_before": sorted({n for _, n, _ in st.elite_buys})}


def quantiles(xs, ps=(0.1, 0.25, 0.5, 0.75, 0.9)):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return {f"p{int(p * 100)}": xs[int(p * (len(xs) - 1))] for p in ps} | {"n": len(xs)}


def build(rows):
    market = Market()
    names = {e.wallet: e.name for e in elite.ELITES}
    market.elite_names = names
    trades = defaultdict(list)
    open_ = {}   # (name, mint) -> trip being built
    trips = defaultdict(list)
    first_rx = last_rx = None
    for row in rows:
        if row.get("k") not in ("trade", "create", "migrate", "pool") or not row.get("mint"):
            continue
        rx = row["rx"]
        first_rx = first_rx or rx
        last_rx = rx
        name = names.get(row.get("u", "")) if row["k"] == "trade" else None
        if name:
            st = market.get(row["mint"])
            ctx = context(st, rx)
            sol = row.get("q", 0) / 1e9
            tokens = row.get("t", 0) / 1e6
            rec = {"rx": rx, "sig": row.get("sig"), "mint": row["mint"], "side": row["side"],
                   "venue": row["v"], "sol": round(sol, 6), "tokens": tokens,
                   "price": row.get("px"), "ctx": ctx}
            trades[name].append(rec)
            key = (name, row["mint"])
            trip = open_.get(key)
            if row["side"] == "buy":
                if trip is None:
                    trip = open_[key] = {"name": name, "mint": row["mint"], "open_rx": rx,
                                         "entry_ctx": ctx, "buys": 0, "sells": 0, "sol_in": 0.0,
                                         "sol_out": 0.0, "tokens_in": 0.0, "tokens_out": 0.0,
                                         "sell_rx": []}
                trip["buys"] += 1
                trip["sol_in"] += sol
                trip["tokens_in"] += tokens
            elif trip is not None:
                trip["sells"] += 1
                trip["sol_out"] += sol
                trip["tokens_out"] += tokens
                trip["sell_rx"].append(rx - trip["open_rx"])
                if trip["tokens_out"] >= trip["tokens_in"] * 0.995:
                    trip["hold_s"] = (rx - trip["open_rx"]) / 1000
                    trip["multiple"] = trip["sol_out"] / trip["sol_in"] if trip["sol_in"] else None
                    trips[name].append(open_.pop(key))
        market.apply(row_to_event(row), rx)
    span_h = ((last_rx or 0) - (first_rx or 0)) / 3_600_000
    return trades, trips, open_, span_h


def summarize(trades, trips, open_, span_h) -> dict:
    out = {"span_hours": round(span_h, 2), "traders": {}}
    for e in elite.ELITES:
        ts, tr = trades.get(e.name, []), trips.get(e.name, [])
        buys = [t for t in ts if t["side"] == "buy"]
        first_buys = [t["entry_ctx"] for t in tr] + [t["entry_ctx"] for k, t in open_.items()
                                                     if k[0] == e.name]
        out["traders"][e.name] = {
            "published": {"style": e.style, "median_hold_s": e.median_hold_s,
                          "median_entry_mcap_usd": e.median_entry_mcap, "win_rate": e.win_rate},
            "trades": len(ts), "buys": len(buys), "trades_per_hour": round(len(ts) / span_h, 1) if span_h else None,
            "venues": dict(Counter(t["venue"] for t in ts)),
            "buy_sol": quantiles([t["sol"] for t in buys]),
            "entry_age_s": quantiles([c.get("age_s") for c in first_buys if c.get("seen_create")]),
            "entry_mcap_sol": quantiles([c.get("mcap_sol") for c in first_buys if c.get("known")]),
            "entry_progress": quantiles([c.get("progress") for c in first_buys if c.get("known")]),
            "entry_buyers_10s": quantiles([c["w10"]["unique_buyers"] for c in first_buys if c.get("known")]),
            "entry_net_sol_60s": quantiles([c["w60"]["net_sol"] for c in first_buys if c.get("known")]),
            "unseen_coin_share": round(sum(1 for c in first_buys if not c.get("known")) / len(first_buys), 3)
            if first_buys else None,
            "closed_trips": len(tr), "open_trips": sum(1 for k in open_ if k[0] == e.name),
            "hold_s": quantiles([t["hold_s"] for t in tr]),
            "multiple": quantiles([t["multiple"] for t in tr]),
            "win_rate": round(sum(1 for t in tr if (t["multiple"] or 0) > 1) / len(tr), 3) if tr else None,
            "sells_per_trip": quantiles([t["sells"] for t in tr]),
            "buys_per_trip": quantiles([t["buys"] for t in tr]),
        }
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="elite dossiers from the tape")
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="")
    args = ap.parse_args(argv)
    trades, trips, open_, span_h = build(read_tape(TAPE_DIR, args.start, args.end))
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in trades.items():
        with open(PROFILE_DIR / f"{name}.trades.jsonl", "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in rows)
    for name, rows in trips.items():
        with open(PROFILE_DIR / f"{name}.trips.jsonl", "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in rows)
    summary = summarize(trades, trips, open_, span_h)
    (PROFILE_DIR / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for name, s in summary["traders"].items():
        print(f"{name:12} trades {s['trades']:5}  trips {s['closed_trips']:4}  win {s['win_rate']}  "
              f"hold_p50 {(s['hold_s'] or {}).get('p50')}  entry_mcap_p50 {(s['entry_mcap_sol'] or {}).get('p50')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
