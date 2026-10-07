"""Live paper-trading runner on free public data. Paper only: it never signs or sends anything.

Feeds
  * public RPC websocket logsSubscribe on Pump.fun, PumpSwap and Raydium LaunchLab
    (every trade, decoded from program logs by chain_events)
  Elite wallets are recognised as the `user` of decoded trades. (A logsSubscribe on the
  wallets themselves is useless: ~300 spam/copy-bot transactions a second mention each one.)
  * GeckoTerminal new_pools every minute: launches on every other Solana DEX
Outputs
  data/tape/...            everything seen, with chain and receive clocks (see tape.py)
  data/paper/<run>/        config.json, one fill ledger per algo, summary.jsonl, status.json

Run:  python -m gemtracker.live [--algos all|name,name] [--latency-ms 1500] [--hours 0]
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import importlib
import json
import pkgutil
import queue
import subprocess
import threading
import time
from collections import OrderedDict, defaultdict
from pathlib import Path

from . import chain_events as ce
from . import elite, net
from .config import DATA_DIR, ROOT
from .market import Market
from .papersim import PaperSim, SimConfig
from .solana import SolanaRpc
from .strategy import Strategy
from .tape import TapeWriter, event_row

# Two free public endpoints. (publicnode lags ~8 s; dRPC free has no logsSubscribe.)
WS_URLS = {"mb": "wss://api.mainnet-beta.solana.com", "sc": "wss://api.mainnet.solana.com"}
# Several connections per stream, deduplicated by signature. Each connection lands on its own
# backend node and nodes differ by seconds: four parallel pump connections to mainnet-beta had
# p50 lag 2.6 / 4.0 / 4.6 / 5.1 s (2026-10-07). Extra copies also cover each other's 1002 drops.
# PumpSwap is ~10x the bytes of the launch streams, so it gets only two.
STREAMS = {"pump": ("mb", "mb", "mb", "sc"), "launchlab": ("mb", "sc"), "pumpswap": ("mb", "mb")}
RECYCLE_SHARE = 0.10  # each minute, a connection first on fewer of its stream's tx reconnects
RECYCLE_MIN_TX = 50


def pick_recycle(wins: dict) -> list[str]:
    """Per stream, the connection that was first least often, when its share is under RECYCLE_SHARE.
    wins: {"<stream>@<endpoint><n>": first arrivals in the last minute}."""
    by_stream = defaultdict(dict)
    for label, n in wins.items():
        by_stream[label.partition("@")[0]][label] = n
    out = []
    for stream, labels in by_stream.items():
        total = sum(labels.values())
        worst = min(labels, key=labels.get)
        if len(labels) == len(STREAMS.get(stream, ())) > 1 and total >= RECYCLE_MIN_TX                 and labels[worst] < RECYCLE_SHARE * total:
            out.append(worst)
    return out
HTTP_URL = "https://api.mainnet-beta.solana.com"
PAPER_DIR = DATA_DIR / "paper"
POOL_CACHE = DATA_DIR / "pool_mints.json"
GT_NEW_POOLS = "https://api.geckoterminal.com/api/v2/networks/solana/new_pools"
TAPE_MIN_SOL = 1.0    # PumpSwap trades below this on coins launched before the run are not taped


def now_ms() -> int:
    return int(time.time() * 1000)


def load_algos(spec: str = "all") -> list[Strategy]:
    """Instantiate strategies from gemtracker/algos/*.py (every Strategy subclass with a name)."""
    from . import algos
    found = []
    for mod in pkgutil.iter_modules(algos.__path__):
        module = importlib.import_module(f"{algos.__name__}.{mod.name}")
        for obj in vars(module).values():
            if (isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy
                    and obj.__module__ == module.__name__ and obj.name != "base"):
                found.append(obj())
    if spec != "all":
        wanted = {s.strip() for s in spec.split(",")}
        found = [s for s in found if s.name in wanted]
    names = [s.name for s in found]
    if len(names) != len(set(names)):
        raise SystemExit(f"duplicate algo names: {names}")
    return found


class SeenSet:
    """Bounded set of recent signatures (both feeds deliver a transaction more than once)."""

    def __init__(self, size: int = 200_000):
        self.size, self.d = size, OrderedDict()

    def add(self, key) -> bool:
        if key in self.d:
            return False
        self.d[key] = None
        if len(self.d) > self.size:
            self.d.popitem(last=False)
        return True


class PoolResolver(threading.Thread):
    """Maps PumpSwap pools and LaunchLab pool states to coin mints (getMultipleAccounts)."""

    def __init__(self, rpc: SolanaRpc, cache: dict):
        super().__init__(daemon=True)
        self.rpc, self.cache = rpc, cache
        self.inbox: queue.Queue = queue.Queue()
        self.done: queue.Queue = queue.Queue()
        self.asked: set = set()
        self.failures = 0

    def want(self, pool: str, venue: str) -> None:
        if pool not in self.asked:
            self.asked.add(pool)
            self.inbox.put((pool, venue))

    def run(self) -> None:
        while True:
            batch = [self.inbox.get()]
            time.sleep(0.5)
            while len(batch) < 100:
                try:
                    batch.append(self.inbox.get_nowait())
                except queue.Empty:
                    break
            for venue in ("pumpswap", "launchlab"):
                pools = [p for p, v in batch if v == venue]
                if pools:
                    self._resolve(pools, venue)

    def _resolve(self, pools: list, venue: str) -> None:
        off = ce.PUMP_AMM_POOL_BASE_MINT if venue == "pumpswap" else ce.LAUNCHLAB_POOL_BASE_MINT
        try:
            res = self.rpc.call("getMultipleAccounts", [pools, {
                "encoding": "base64", "dataSlice": {"offset": off, "length": 32},
                "commitment": "confirmed"}]) or {}
        except Exception:
            self.failures += 1
            for p in pools:  # let them be asked again later
                self.asked.discard(p)
            return
        for pool, acc in zip(pools, res.get("value") or []):
            if acc and acc.get("data"):
                raw = base64.b64decode(acc["data"][0])
                if len(raw) == 32:
                    self.done.put((pool, ce.b58encode(raw)))


class Runner:
    def __init__(self, strategies, cfg: SimConfig, run_dir: Path, tape: bool = True):
        self.market = Market()
        self.market.elite_names = {e.wallet: e.name for e in elite.ELITES}
        self.rpc = SolanaRpc(HTTP_URL)
        self.pool_cache = json.loads(POOL_CACHE.read_text(encoding="utf-8")) if POOL_CACHE.exists() else {}
        self.market.pool_mint.update(self.pool_cache)
        self.resolver = PoolResolver(self.rpc, self.pool_cache)
        self.parked: dict[str, list] = defaultdict(list)  # pool -> events awaiting its mint
        self.q: asyncio.Queue | None = None
        self.seen = SeenSet()
        self.tape = TapeWriter() if tape else None
        self.run_dir = run_dir
        self._sol_usd = 0.0
        self._sol_usd_at = 0.0
        self.sim = PaperSim(strategies, cfg, self.sol_usd, run_dir)
        self.stats = defaultdict(int)
        self.lag = defaultdict(list)  # venue -> receive minus chain time, ms (latency realism)
        self.loop = defaultdict(list)  # our own delays, ms: queue wait, tick cost, sleep overshoot
        self.wins = defaultdict(int)  # connection label -> tx it delivered first, this minute
        self.recycle = set()  # connection labels to reconnect on their next message
        self.labels = []
        self.started = now_ms()

    # ----- prices -----
    def sol_usd(self) -> float:
        if time.time() - self._sol_usd_at > 600 or not self._sol_usd:
            for url, params in (("https://api.exchange.coinbase.com/products/SOL-USD/ticker", None),
                                ("https://data-api.binance.vision/api/v3/ticker/price",
                                 {"symbol": "SOLUSDT"})):
                try:
                    self._sol_usd = float(net.get_json(url, params=params, retries=1)["price"])
                    break
                except Exception:
                    continue
            self._sol_usd_at = time.time()
            if not self._sol_usd:
                raise RuntimeError("no SOL/USD price")
        return self._sol_usd

    # ----- feeds -----
    async def feed(self, label: str, mentions: list[str], url: str) -> None:
        import websockets
        backoff = 1
        while True:
            try:
                async with websockets.connect(url, max_size=2 ** 24, ping_interval=20,
                                              open_timeout=20) as ws:
                    subs = {}
                    for i, key in enumerate(mentions):
                        await ws.send(json.dumps({"jsonrpc": "2.0", "id": i, "method": "logsSubscribe",
                                                  "params": [{"mentions": [key]},
                                                             {"commitment": "processed"}]}))
                    backoff = 1
                    self.stats[f"connect_{label}"] += 1
                    while True:
                        msg = json.loads(await asyncio.wait_for(ws.recv(), 60))
                        if label in self.recycle:  # a slow node: reconnect to draw another
                            self.recycle.discard(label)
                            self.stats[f"recycle_{label}"] += 1
                            break
                        if "id" in msg and "result" in msg:
                            subs[msg["result"]] = mentions[msg["id"]]
                            continue
                        params = msg.get("params")
                        if not params:
                            continue
                        res = params["result"]
                        await self.q.put((now_ms(), label, subs.get(params["subscription"], ""),
                                          res["context"]["slot"], res["value"]))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.stats[f"drop_{label}"] += 1
                self.stats["last_drop"] = f"{label} {type(exc).__name__} {str(exc)[:60]}"
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def gecko(self) -> None:
        seen = SeenSet(50_000)
        while True:
            try:
                data = await asyncio.to_thread(net.get_json, GT_NEW_POOLS, retries=1)
                for pool in data.get("data") or []:
                    a = pool.get("attributes") or {}
                    rel = pool.get("relationships") or {}
                    if not seen.add(a.get("address")):
                        continue
                    base = ((rel.get("base_token") or {}).get("data") or {}).get("id", "")
                    dex = ((rel.get("dex") or {}).get("data") or {}).get("id", "")
                    vol = a.get("volume_usd") or {}
                    tx = (a.get("transactions") or {}).get("m5") or {}
                    self._write({"rx": now_ms(), "k": "gt_pool", "dex": dex, "pool": a.get("address"),
                                 "mint": base.removeprefix("solana_"), "name": a.get("name"),
                                 "created": a.get("pool_created_at"), "fdv": a.get("fdv_usd"),
                                 "liq": a.get("reserve_in_usd"), "px": a.get("base_token_price_usd"),
                                 "vol_m5": vol.get("m5"), "buys_m5": tx.get("buys"),
                                 "sells_m5": tx.get("sells")})
                    self.stats[f"gt_{dex}"] += 1
            except Exception:
                self.stats["gt_errors"] += 1
            await asyncio.sleep(60)

    # ----- processing -----
    def _write(self, row: dict) -> None:
        if self.tape:
            self.tape.write(row)

    def _interesting(self, ev, st) -> bool:
        """Tape everything except PumpSwap dust on old coins (the bulk of the firehose)."""
        if ev.venue != "pumpswap" or ev.kind != "trade":
            return True
        return (ev.user in self.market.elite_names or ev.quote >= TAPE_MIN_SOL * 1e9
                or bool(st and st.seen_create))

    def handle_event(self, ev, rx: int, live: bool = True) -> None:
        if not ev.mint and ev.pool:
            mint = self.market.pool_mint.get(ev.pool)
            if not mint:
                if ev.kind == "pool":
                    mint = ev.mint
                else:
                    if len(self.parked[ev.pool]) < 50:
                        self.parked[ev.pool].append((ev, rx))
                    self.resolver.want(ev.pool, ev.venue)
                    self.stats["parked"] += 1
                    return
            ev.mint = mint
        if ev.kind == "pool" and ev.pool:
            self.market.pool_mint[ev.pool] = ev.mint
            self.pool_cache[ev.pool] = ev.mint
        if live:
            self.sim.settle(ev.mint, rx, self.market)
        st = self.market.apply(ev, rx)
        if self._interesting(ev, st):
            self._write(event_row(ev, rx))
            self.stats["taped"] += 1
        self.stats[f"{ev.venue}_{ev.kind}"] += 1
        if ev.user in self.market.elite_names:
            self.stats["elite_trades"] += 1
        if not live or st is None:
            return
        if ev.kind == "create" and st.seen_create:
            self.sim.dispatch("on_create", self.market, rx, st)
        elif ev.kind == "trade":
            self.sim.dispatch("on_trade", self.market, rx, st, ev)

    def drain_threads(self) -> None:
        while not self.resolver.done.empty():
            pool, mint = self.resolver.done.get()
            self.market.pool_mint[pool] = mint
            self.pool_cache[pool] = mint
            for ev, rx in sorted(self.parked.pop(pool, []), key=lambda x: x[1]):
                ev.mint = mint
                self.handle_event(ev, rx, live=False)  # late: market state only, no decisions

    def process(self, item) -> None:
        rx, label, key, slot, value = item
        if len(self.loop["queue_wait"]) < 20_000:
            self.loop["queue_wait"].append(now_ms() - rx)
        sig = value.get("signature", "")
        if value.get("err") or not self.seen.add(sig):
            return
        self.stats["first_" + label.rpartition("@")[2].rstrip("0123456789")] += 1
        self.wins[label] += 1
        for ev in ce.parse_logs(sig, value.get("logs") or [], slot):
            if ev.ts and len(self.lag[ev.venue]) < 20_000:
                self.lag[ev.venue].append(rx - ev.ts * 1000)
            self.handle_event(ev, rx)

    async def consume(self) -> None:
        while True:
            item = await self.q.get()
            self.process(item)
            if self.q.qsize() > 20_000:
                self.stats["backlog_drops"] += 1
                self.q.get_nowait()

    async def clock(self, hours: float) -> None:
        last_status = last_summary = time.time()
        end = time.time() + hours * 3600 if hours else None
        while end is None or time.time() < end:
            before = time.perf_counter()
            await asyncio.sleep(1)
            t = now_ms()
            self.loop["sleep_overshoot"].append(int((time.perf_counter() - before - 1) * 1000))
            self.drain_threads()
            self.sim.settle(None, t, self.market)
            self.sim.dispatch("on_tick", self.market, t)
            self.loop["tick_cost"].append(now_ms() - t)
            if time.time() - last_status >= 60:
                last_status = time.time()
                self.status(t)
            if time.time() - last_summary >= 3600:
                last_summary = time.time()
                with open(self.run_dir / "summary.jsonl", "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"t": t, "rows": self.sim.summary(self.market)}) + "\n")

    def status(self, t: int) -> None:
        if self.tape:
            self.tape.flush()
        held = {m for b in self.sim.books.values() for m in b.positions}
        held |= {p.intent.mint for b in self.sim.books.values() for p in b.pending}
        self.stats["pruned"] += self.market.prune(t, held)
        lag = {}
        for venue, xs in self.lag.items():
            xs.sort()
            lag[venue] = {f"p{int(p * 100)}": xs[int(p * (len(xs) - 1))] for p in (0.5, 0.9, 0.99)}
        self.lag.clear()
        loop = {}
        for k, xs in self.loop.items():
            xs.sort()
            loop[k] = {"p50": xs[len(xs) // 2], "p90": xs[int(0.9 * (len(xs) - 1))], "max": xs[-1]} if xs else {}
        self.loop.clear()
        # Every connection appears, so a live connection with no wins counts as the slowest.
        wins = {label: self.wins.get(label, 0) for label in self.labels}
        self.recycle.update(pick_recycle(wins))
        self.wins.clear()
        POOL_CACHE.parent.mkdir(parents=True, exist_ok=True)
        POOL_CACHE.write_text(json.dumps(self.pool_cache), encoding="utf-8")
        status = {"t": t, "uptime_min": round((t - self.started) / 60000, 1),
                  "queue": self.q.qsize(), "tokens": len(self.market.tokens),
                  "pools_known": len(self.market.pool_mint), "parked": sum(map(len, self.parked.values())),
                  "resolver_failures": self.resolver.failures,
                  "feed_lag_ms": lag, "loop_ms": loop,
                  "sol_usd": self._sol_usd, "stats": dict(self.stats),
                  "algos": self.sim.summary(self.market)}
        (self.run_dir / "status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")

    async def main(self, hours: float) -> None:
        import websockets  # noqa: F401  fail here; inside a feed task a missing module dies silently
        self.q = asyncio.Queue()
        self.resolver.start()
        # Separate connections per program so the PumpSwap firehose cannot delay Pump.fun launches.
        conns = [(f"{name}@{ep}{i}", prog, WS_URLS[ep]) for prog, name in ce.PROGRAMS.items()
                 for i, ep in enumerate(STREAMS[name])]
        self.labels = [label for label, _, _ in conns]
        tasks = [asyncio.create_task(self.feed(label, [prog], url)) for label, prog, url in conns]
        tasks += [asyncio.create_task(self.gecko()), asyncio.create_task(self.consume())]
        try:
            await self.clock(hours)
        finally:
            for task in tasks:
                task.cancel()
            self.status(now_ms())
            if self.tape:
                self.tape.close()


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def below_normal_priority() -> None:
    """Heavy jobs run at BelowNormal priority (team rule); Windows only."""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        k32.SetPriorityClass(ctypes.c_void_p(k32.GetCurrentProcess()), 0x4000)
    except Exception:
        pass


def main(argv=None) -> int:
    below_normal_priority()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--algos", default="all")
    ap.add_argument("--latency-ms", type=int, default=2500,
                    help="decision to fill, in receive time: feed lag p90 (~2.1 s) + send (~0.5 s)")
    ap.add_argument("--tx-fee-sol", type=float, default=0.001)
    ap.add_argument("--hours", type=float, default=0, help="stop after this long (0 = run until killed)")
    ap.add_argument("--run", default="", help="run folder name (default: timestamp)")
    ap.add_argument("--no-tape", action="store_true")
    args = ap.parse_args(argv)
    strategies = load_algos(args.algos)
    cfg = SimConfig(latency_ms=args.latency_ms, tx_fee_sol=args.tx_fee_sol)
    run = args.run or time.strftime("%Y%m%d-%H%M%S")
    run_dir = PAPER_DIR / run
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps({
        "commit": _git_commit(), "started": now_ms(), "sim": vars(cfg),
        "algos": [s.name for s in strategies], "feeds": ["rpc-logs:" + json.dumps(STREAMS), "geckoterminal"],
        "paper_only": True}, indent=1), encoding="utf-8")
    runner = Runner(strategies, cfg, run_dir, tape=not args.no_tape)
    print(f"paper run {run}: {len(strategies)} algos, latency {cfg.latency_ms} ms -> {run_dir}",
          flush=True)
    try:
        asyncio.run(runner.main(args.hours))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
