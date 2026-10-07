"""Replay the recorded tape through the same Market + PaperSim the live runner uses.

Strictly in receive order: an algo sees each row at its `rx` time, and its orders fill at
rx + latency against the state as received by then, exactly as live. Use it to develop
and freeze algos on one tape span, then test once on a later span nobody has looked at.

    python -m gemtracker.replay --algos all --start 20261007/17 --end 20261007/23
"""
from __future__ import annotations

import argparse
import json

from .chain_events import WSOL, ChainEvent
from .live import load_algos
from .market import Market
from .papersim import PaperSim, SimConfig
from .tape import TAPE_DIR, read_tape

FIELDS = {"k": "kind", "v": "venue", "sig": "signature", "i": "index", "slot": "slot", "ts": "ts",
          "mint": "mint", "pool": "pool", "u": "user", "side": "side", "q": "quote", "t": "tokens",
          "rq": "reserve_quote", "rb": "reserve_base", "fee": "fee_bps", "pg": "progress",
          "px": "price", "qm": "quote_mint", "x": "extra"}


def row_to_event(row: dict) -> ChainEvent:
    kw = {FIELDS[k]: v for k, v in row.items() if k in FIELDS}
    kw.setdefault("signature", "")
    kw.setdefault("index", 0)
    kw.setdefault("quote_mint", WSOL)
    return ChainEvent(**kw)


def replay(strategies, cfg: SimConfig, rows, sol_usd: float, elite_names: dict | None = None,
           out_dir=None, probe=None):
    """Run strategies over tape rows (an iterable in rx order). Returns (sim, market).
    `probe(sim, market, now_ms)`, if given, runs after every one-second tick (for sampling
    equity or pruning the market the way the live runner does)."""
    market = Market()
    market.elite_names = dict(elite_names or {})
    sim = PaperSim(strategies, cfg, lambda: sol_usd, out_dir)
    next_tick = None
    for row in rows:
        if row.get("k") not in ("trade", "create", "migrate", "pool") or not row.get("mint"):
            continue
        rx = row["rx"]
        if next_tick is None:
            next_tick = rx - rx % 1000 + 1000
        while next_tick <= rx:  # the live clock ticks once a second
            sim.settle(None, next_tick, market)
            sim.dispatch("on_tick", market, next_tick)
            if probe is not None:
                probe(sim, market, next_tick)
            next_tick += 1000
        ev = row_to_event(row)
        sim.settle(ev.mint, rx, market)
        st = market.apply(ev, rx)
        if st is None:
            continue
        if ev.kind == "create":
            sim.dispatch("on_create", market, rx, st)
        elif ev.kind == "trade":
            sim.dispatch("on_trade", market, rx, st, ev)
    if next_tick is not None:  # let orders still in flight arrive
        sim.settle(None, next_tick + cfg.latency_ms, market)
    return sim, market


def main(argv=None) -> int:
    from . import elite
    ap = argparse.ArgumentParser(description="replay the tape through paper algos")
    ap.add_argument("--algos", default="all")
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="")
    ap.add_argument("--latency-ms", type=int, default=SimConfig.latency_ms)
    ap.add_argument("--sol-usd", type=float, required=True, help="fixed SOL/USD for the span")
    args = ap.parse_args(argv)
    cfg = SimConfig(latency_ms=args.latency_ms)
    sim, market = replay(load_algos(args.algos), cfg, read_tape(TAPE_DIR, args.start, args.end),
                         args.sol_usd, {e.wallet: e.name for e in elite.ELITES})
    for row in sim.summary(market):
        print(json.dumps(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
