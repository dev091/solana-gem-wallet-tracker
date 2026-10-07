"""Paced, resumable full-history fetcher for the elite wallets, on the free public RPC only.

    python -m gemtracker.history --wallet decu [--all] [--until-slot N] [--report]

Output in data/history/<name>/:
  state.json      feed cursors + counters, so a restart resumes where it stopped
  sigs.jsonl      raw getSignaturesForAddress pages, one line per page
  processed.txt   every signature already turned into swaps (or found not to be one)
  swaps.jsonl     slot, block_time, tx_index, sig, mint, side, sol, tokens, fee_sol, rent_sol, venue
  trips.jsonl     flat-to-flat round trips per mint (scoreboard format: open_rx, hold_s, sol_in, sol_out)
  monthly.json    per US Eastern month: PnL, SOL deployed, return per SOL, trips, win rate, open bags
  fetch.log       progress log; touch STOP in the same folder to stop cleanly

Two ways to list a wallet's transactions:
  wallet  page the wallet's own signatures. Fine for quiet wallets (a few hundred tx a day).
  via     the busiest elites' addresses are referenced by millions of third-party transactions a day
          (copy bots; Decu ~8.6M signatures/day, 80% failed, measured 2026-10-07), which no free RPC
          can page. Instead page the wallet's own Pump.fun and PumpSwap user_volume_accumulator PDAs
          (one write per buy, nobody else touches them), then page the wallet's token account of every
          mint found, which holds all its buys and sells of that mint on any venue. Mints traded only
          outside Pump.fun / PumpSwap, or before the accumulators existed, are not seen.
  auto    (default) picks via when the newest 1000 signatures span less than a day.

Swaps are venue-agnostic, read from balance changes: SOL = the wallet's lamport change plus the lamport
change of every token account it owns (wrapped SOL and token-account rent are the wallet's own money
moving between its accounts), with the network fee added back when the wallet paid it. SOL out + one
coin in = buy, coin out + SOL in = sell. Jito tips and trading-bot fees stay inside `sol`.

Rate limits are hard rules: one request at a time, ~2 req/s, exponential backoff with jitter on
429 / 5xx, a long pause (10 min and up) on the RPC's 413 "data allowance" error. Free public endpoints
only; no keys, proxies or header games.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from . import elite, net, util
from .config import DATA_DIR, IGNORED_MINTS, STABLES
from .pumpfun import find_program_address
from .scoreboard import et_day

HISTORY_DIR = DATA_DIR / "history"
# The recorder's HTTP calls go to api.mainnet-beta; this sibling public endpoint spreads the load.
DEFAULT_RPC = "https://api.mainnet.solana.com"
USER_AGENT = "gemtracker-history/1.0 (read-only backfill)"
LAMPORTS = 1_000_000_000
WSOL = "So11111111111111111111111111111111111111112"
PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
JUPITER = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
VENUES = {  # checked in this order; an aggregator route wins over the pools it calls
    JUPITER: "jupiter",
    PUMP: "pump",
    PUMP_AMM: "pumpswap",
    "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj": "launchlab",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "raydium",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "raydium",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "raydium",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "orca",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9t8tquNWV": "meteora",
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": "meteora",
    "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG": "meteora",
    "dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN": "meteora",
    "MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG": "moonshot",
}
MIN_SWAP_SOL = 1e-5        # smaller SOL moves next to a token change are transfers, not trades
DUST_FRAC = 0.001          # a trip closes when under 0.1% of its peak tokens is left
REPORT_EVERY_S = 1800      # rebuild trips.jsonl / monthly.json while fetching
NOISY_PAGE_SPAN_S = 86_400 # 1000 newest signatures within a day = address spammed by others

# RPC pacing
RPS = 2.0
BACKOFF_BASE_S, BACKOFF_CAP_S = 2.0, 120.0
ALLOWANCE_PAUSE_S, ALLOWANCE_PAUSE_CAP_S = 600.0, 3600.0
RETRY_RPC_CODES = {429, -32429, -32005, -32004, -32014, -32016}
MISSING_RPC_CODES = {-32007, -32009, -32011}  # skipped slot / not in long-term storage / no tx history


class RpcError(Exception):
    pass


def below_normal_priority() -> None:
    """Heavy jobs run at BelowNormal priority (team rule); Windows only."""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        k32.SetPriorityClass(ctypes.c_void_p(k32.GetCurrentProcess()), 0x4000)
    except Exception:
        pass


# ---------------------------------------------------------------- RPC

class PacedRpc:
    """One JSON-RPC request at a time, at most `rps` per second, polite backoff."""

    def __init__(self, url: str = DEFAULT_RPC, rps: float = RPS, post=None, sleep=time.sleep,
                 clock=time.monotonic, rng=random.random, log=print, max_attempts: int = 12):
        if re.search(r"helius|api[-_]?key", url, re.I):
            raise ValueError("free public endpoints only")
        self.url, self.base_interval = url, 1.0 / rps
        self.interval = self.base_interval
        self.post = post or (lambda u, body: net.post_json(u, body, retries=0, timeout=60,
                                                           headers={"User-Agent": USER_AGENT}))
        self.sleep, self.clock, self.rng, self.log = sleep, clock, rng, log
        self.max_attempts = max_attempts
        self.next_at = 0.0
        self.ok_streak = 0
        self.allowance_streak = 0
        self.stats = Counter()          # requests, 429, 413, 5xx, net
        self.recent = deque(maxlen=600)  # clock() of recent requests, for the measured rate
        self._id = 0

    def rate(self, window: float = 60.0) -> float:
        now = self.clock()
        n = sum(1 for t in self.recent if now - t <= window)
        span = min(window, now - self.recent[0]) if self.recent else 0
        return n / span if span > 0 else 0.0

    def _pace(self) -> None:
        now = self.clock()
        if self.next_at > now:
            self.sleep(self.next_at - now)
        self.next_at = max(now, self.next_at) + self.interval

    def _backoff(self, kind: str, attempt: int) -> None:
        self.stats[kind] += 1
        self.ok_streak = 0
        self.interval = min(self.interval * 1.5, 4.0)  # slow down for a while
        delay = min(BACKOFF_BASE_S * 2 ** attempt, BACKOFF_CAP_S) * (0.5 + self.rng())
        self.log(f"   rpc {kind}: backing off {delay:.0f}s (pace now {1 / self.interval:.2f} req/s)")
        self.sleep(delay)

    def _allowance_pause(self) -> None:
        self.stats["413"] += 1
        self.allowance_streak += 1
        self.interval = min(self.interval * 2, 4.0)
        pause = min(ALLOWANCE_PAUSE_S * 2 ** (self.allowance_streak - 1), ALLOWANCE_PAUSE_CAP_S)
        self.log(f"   rpc 413 data allowance used up: pausing {pause / 60:.0f} min")
        self.sleep(pause)

    def call(self, method: str, params: list):
        for attempt in range(self.max_attempts):
            self._pace()
            self._id += 1
            self.stats["requests"] += 1
            self.recent.append(self.clock())
            try:
                reply = self.post(self.url, {"jsonrpc": "2.0", "id": self._id, "method": method,
                                             "params": params})
            except net.HttpError as exc:
                if exc.status == 413 or "allowance" in exc.body.lower():
                    self._allowance_pause()
                elif exc.status == 429:
                    self._backoff("429", attempt)
                elif exc.status == 0 or exc.status >= 500 or exc.status in (408, 425):
                    self._backoff("5xx" if exc.status else "net", attempt)
                else:
                    raise RpcError(f"{method}: {exc}") from None
                continue
            if not isinstance(reply, dict):
                self._backoff("net", attempt)
                continue
            error = reply.get("error")
            if not error:
                self.allowance_streak = 0
                self.ok_streak += 1
                if self.ok_streak % 200 == 0 and self.interval > self.base_interval:
                    self.interval = max(self.base_interval, self.interval / 1.25)
                return reply.get("result")
            code, message = error.get("code"), str(error.get("message", ""))
            if "allowance" in message.lower():
                self._allowance_pause()
            elif code in (429, -32429):
                self._backoff("429", attempt)
            elif code in RETRY_RPC_CODES:
                self._backoff("busy", attempt)
            elif code in MISSING_RPC_CODES:
                return None
            else:
                raise RpcError(f"{method} failed: {message} (code {code})")
        raise RpcError(f"{method}: gave up after {self.max_attempts} attempts")


# ---------------------------------------------------------------- swap derivation

def account_keys(tx: dict) -> list:
    """All account keys, lookup-table ones included, for json and jsonParsed encodings."""
    message = (tx.get("transaction") or {}).get("message") or {}
    raw = message.get("accountKeys") or []
    keys = [k.get("pubkey") if isinstance(k, dict) else k for k in raw]
    if raw and not isinstance(raw[0], dict):
        loaded = (tx.get("meta") or {}).get("loadedAddresses") or {}
        keys += list(loaded.get("writable") or []) + list(loaded.get("readonly") or [])
    return keys


def programs(tx: dict, keys: list) -> set:
    message = (tx.get("transaction") or {}).get("message") or {}
    inner = [ix for group in (tx.get("meta") or {}).get("innerInstructions") or []
             for ix in group.get("instructions") or []]
    out = set()
    for ix in list(message.get("instructions") or []) + inner:
        if "programId" in ix:
            out.add(ix["programId"])
        elif isinstance(ix.get("programIdIndex"), int) and ix["programIdIndex"] < len(keys):
            out.add(keys[ix["programIdIndex"]])
    return out


def venue_of(progs: set) -> str:
    return next((name for pid, name in VENUES.items() if pid in progs), "other")


def derive_swaps(tx: dict | None, wallet: str) -> tuple[str, list, dict]:
    """(kind, swap rows, {token account: mint} the wallet owns in this tx).

    kind: swap | failed | missing | nonswap | multi_mint | other_asset."""
    if not tx:
        return "missing", [], {}
    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return "failed", [], {}
    keys = account_keys(tx)
    pre, post = meta.get("preBalances") or [], meta.get("postBalances") or []

    def lamport_delta(i):
        return post[i] - pre[i] if 0 <= i < len(pre) and i < len(post) else 0

    accounts, raw, decimals = {}, defaultdict(int), {}
    for sign, balances in ((-1, meta.get("preTokenBalances")), (1, meta.get("postTokenBalances"))):
        for bal in balances or []:
            if bal.get("owner") != wallet or not bal.get("mint"):
                continue
            amount = bal.get("uiTokenAmount") or {}
            raw[bal["mint"]] += sign * int(amount.get("amount") or 0)
            decimals[bal["mint"]] = int(amount.get("decimals") or 0)
            accounts[bal.get("accountIndex")] = bal["mint"]
    owned = {keys[i]: m for i, m in accounts.items() if isinstance(i, int) and i < len(keys)}

    wallet_lamports = lamport_delta(keys.index(wallet)) if wallet in keys else 0
    # Token accounts' lamports = wrapped SOL + rent: both are the wallet's money changing pockets.
    accounts_lamports = sum(lamport_delta(i) for i in accounts if isinstance(i, int))
    wsol_raw = raw.pop(WSOL, 0)
    fee = int(meta.get("fee") or 0) if keys and keys[0] == wallet else 0
    rent = accounts_lamports - wsol_raw
    sol = (wallet_lamports + accounts_lamports + fee) / LAMPORTS
    coins = {m: a / 10 ** decimals.get(m, 0) for m, a in raw.items() if a}
    if not coins:
        return "nonswap", [], owned
    if any(m in IGNORED_MINTS or m in STABLES for m in coins):
        return "other_asset", [], owned
    if len(coins) > 1:
        return "multi_mint", [], owned
    (mint, tokens), = coins.items()
    if tokens > 0 and sol < -MIN_SWAP_SOL:
        side = "buy"
    elif tokens < 0 and sol > MIN_SWAP_SOL:
        side = "sell"
    else:
        return "nonswap", [], owned
    signature = ((tx.get("transaction") or {}).get("signatures") or [""])[0]
    row = {"slot": tx.get("slot") or 0, "block_time": tx.get("blockTime"),
           "tx_index": tx.get("transactionIndex"), "sig": signature, "mint": mint, "side": side,
           "sol": round(abs(sol), 9), "tokens": abs(tokens), "fee_sol": fee / LAMPORTS,
           "rent_sol": round(rent / LAMPORTS, 9), "venue": venue_of(programs(tx, keys))}
    return "swap", [row], owned


# ---------------------------------------------------------------- trips + monthly

def _month(ms: int) -> str:
    return et_day(ms).strftime("%Y-%m")


def build_trips(swaps: list, name: str = "") -> tuple[list, list, dict]:
    """Flat-to-flat round trips per mint. Returns (trips, open bags, orphan sells).

    A trip opens on the first buy while flat and closes when under DUST_FRAC of its peak tokens is
    left; its PnL is SOL out - SOL in, so no cost-basis choice is involved. Average cost is used only
    to split an open bag's cost between the sold and the still-held tokens."""
    seen, rows = set(), []
    for s in swaps:
        if (s["sig"], s["mint"]) not in seen:
            seen.add((s["sig"], s["mint"]))
            rows.append(s)
    rows.sort(key=lambda s: (s["slot"], s.get("tx_index") or 0, s["sig"]))
    pos, trips, orphans = {}, [], {"n": 0, "sol": 0.0, "by_month": defaultdict(float)}
    for s in rows:
        ms = int((s.get("block_time") or 0) * 1000)
        p = pos.get(s["mint"])
        if s["side"] == "buy":
            if p is None:
                p = pos[s["mint"]] = {"name": name, "mint": s["mint"], "open_rx": ms, "open_sig": s["sig"],
                                      "tokens": 0.0, "peak": 0.0, "cost": 0.0, "sol_in": 0.0,
                                      "sol_out": 0.0, "fees_sol": 0.0, "n_buys": 0, "n_sells": 0,
                                      "venues": Counter()}
            p["tokens"] += s["tokens"]
            p["peak"] = max(p["peak"], p["tokens"])
            p["cost"] += s["sol"]
            p["sol_in"] += s["sol"]
            p["n_buys"] += 1
        elif p is None:  # coins that arrived without a SOL buy (transfer, token swap, airdrop)
            orphans["n"] += 1
            orphans["sol"] += s["sol"]
            orphans["by_month"][_month(ms)] += s["sol"]
            continue
        else:
            sold = min(s["tokens"], p["tokens"])
            p["cost"] -= p["cost"] * (sold / p["tokens"] if p["tokens"] else 1.0)
            p["tokens"] -= sold
            p["sol_out"] += s["sol"]
            p["n_sells"] += 1
        p["fees_sol"] += s.get("fee_sol", 0.0)
        p["venues"][s.get("venue", "other")] += 1
        if s["side"] == "sell" and p["tokens"] <= DUST_FRAC * p["peak"]:
            trips.append(_close(p, ms))
            del pos[s["mint"]]
    bags = [{"mint": p["mint"], "open_rx": p["open_rx"], "sol_in": round(p["sol_in"], 9),
             "sol_out": round(p["sol_out"], 9), "tokens_left": p["tokens"], "cost_left": round(p["cost"], 9),
             "status": "unrealized-unknown"} for p in pos.values()]
    orphans["by_month"] = dict(orphans["by_month"])
    return trips, bags, orphans


def _close(p: dict, ms: int) -> dict:
    return {"name": p["name"], "mint": p["mint"], "open_rx": p["open_rx"], "close_rx": ms,
            "hold_s": (ms - p["open_rx"]) / 1000, "sol_in": round(p["sol_in"], 9),
            "sol_out": round(p["sol_out"], 9), "pnl_sol": round(p["sol_out"] - p["sol_in"], 9),
            "fees_sol": round(p["fees_sol"], 9), "n_buys": p["n_buys"], "n_sells": p["n_sells"],
            "venue": p["venues"].most_common(1)[0][0], "open_sig": p["open_sig"]}


def monthly_summary(trips: list, bags: list, orphans: dict, sol_usd: dict | None = None) -> dict:
    """Per US Eastern month (trips booked on the month they closed, bags on the month they opened)."""
    months = defaultdict(lambda: {"pnl_sol": 0.0, "fees_sol": 0.0, "deployed_sol": 0.0, "trips": 0,
                                  "wins": 0, "open_bags": 0, "open_bag_sol_in": 0.0, "orphan_sell_sol": 0.0})
    for t in trips:
        m = months[_month(t["close_rx"])]
        m["pnl_sol"] += t["pnl_sol"]
        m["fees_sol"] += t["fees_sol"]
        m["deployed_sol"] += t["sol_in"]
        m["trips"] += 1
        m["wins"] += t["pnl_sol"] > 0
    for b in bags:
        m = months[_month(b["open_rx"])]
        m["open_bags"] += 1
        m["open_bag_sol_in"] += b["sol_in"]
    for month, sol in (orphans.get("by_month") or {}).items():
        months[month]["orphan_sell_sol"] += sol
    out = {}
    for month in sorted(months):
        m = months[month]
        m["pnl_net_sol"] = m["pnl_sol"] - m["fees_sol"]
        m["return_per_sol"] = m["pnl_sol"] / m["deployed_sol"] if m["deployed_sol"] else None
        m["win_rate"] = m["wins"] / m["trips"] if m["trips"] else None
        if sol_usd and month in sol_usd:
            m["sol_usd_approx"] = sol_usd[month]
            m["pnl_usd_approx"] = m["pnl_sol"] * sol_usd[month]
        out[month] = {k: round(v, 6) if isinstance(v, float) else v for k, v in m.items()}
    return out


def month_sol_usd() -> dict:
    """{YYYY-MM: SOL/USD volume-weighted average} from Binance's free public monthly candles (UTC months)."""
    try:
        rows = net.get_json("https://data-api.binance.vision/api/v3/klines",
                            params={"symbol": "SOLUSDT", "interval": "1M", "limit": 60}, retries=1,
                            headers={"User-Agent": USER_AGENT})
        out = {}
        for r in rows or []:
            month = datetime.fromtimestamp(r[0] / 1000, tz=timezone.utc).strftime("%Y-%m")
            volume, quote = float(r[5]), float(r[7])
            out[month] = round(quote / volume, 4) if volume else float(r[4])
        return out
    except Exception:
        return {}


# ---------------------------------------------------------------- fetcher

def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def resolve(key: str) -> tuple[str, str]:
    """(name, wallet) from an elite name (any case) or a raw wallet address."""
    for e in elite.ELITES:
        if key.lower() in (e.name.lower(), slug(e.name)) or key == e.wallet:
            return e.name, e.wallet
    try:
        if len(util.b58decode(key)) == 32:
            return key[:8], key
    except (KeyError, ValueError):
        pass
    raise SystemExit(f"unknown wallet {key!r}")


def accumulators(wallet: str) -> list:
    """The wallet's Pump.fun and PumpSwap user_volume_accumulator PDAs (written by its own buys)."""
    seed = [b"user_volume_accumulator", util.b58decode(wallet)]
    return [find_program_address(seed, PUMP)[0], find_program_address(seed, PUMP_AMM)[0]]


class Fetcher:
    def __init__(self, name: str, wallet: str, rpc, out_dir: Path, mode: str = "auto",
                 until_slot: int = 0, log=print, clock=time.time, status_every_s: float = 60.0):
        self.name, self.wallet, self.rpc, self.dir = name, wallet, rpc, out_dir
        self.until_slot, self.log, self.clock = until_slot, log, clock
        self.status_every_s = status_every_s
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        self.state = self._load_state(mode)
        self.processed = self._load_lines("processed.txt")
        self.atas_done = self._load_lines("atas_done.txt")
        self._last_status = self.clock()
        self._started = self.clock()
        self._last_report = self.clock()
        self._requests_at_start = 0

    # -- persistence
    def _load_state(self, mode: str) -> dict:
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if state.get("wallet") != self.wallet:
                raise SystemExit(f"{self.state_path} belongs to another wallet")
            return state
        return {"name": self.name, "wallet": self.wallet, "mode": mode, "feeds": {},
                "counts": {}, "sig_earliest_bt": None, "sig_latest_bt": None, "tx_earliest_bt": None,
                "phase": "sigs", "until_slot": self.until_slot}

    def _load_lines(self, fname: str) -> set:
        path = self.dir / fname
        return set(path.read_text(encoding="utf-8").split()) if path.exists() else set()

    def _append(self, fname: str, lines: list) -> None:
        if lines:
            with open(self.dir / fname, "a", encoding="utf-8") as fh:
                fh.write("".join(line + "\n" for line in lines))

    def save(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def count(self, key: str, n: int = 1) -> None:
        self.state["counts"][key] = self.state["counts"].get(key, 0) + n

    def stop_requested(self) -> bool:
        return (self.dir / "STOP").exists()

    # -- mode + feeds
    def setup(self) -> None:
        st = self.state
        if st["feeds"]:
            return
        mode = st["mode"]
        if mode == "auto":
            page = self.rpc.call("getSignaturesForAddress",
                                 [self.wallet, {"limit": 1000, "commitment": "finalized"}]) or []
            span = (page[0].get("blockTime") or 0) - (page[-1].get("blockTime") or 0) if page else 0
            mode = "via" if len(page) == 1000 and span < NOISY_PAGE_SPAN_S else "wallet"
            self.log(f"{self.name}: newest 1000 signatures span {span}s -> mode {mode}")
        st["mode"] = mode
        feeds = accumulators(self.wallet) if mode == "via" else [self.wallet]
        st["feeds"] = {a: {"before": None, "done": False, "sigs": 0, "ok": 0} for a in feeds}
        self.save()

    # -- phase 1: signatures
    def page_signatures(self, address: str, cursor: dict, tag: str) -> list:
        """Fetch one page older than cursor['before']; appends it to sigs.jsonl. Returns ok infos."""
        cfg = {"limit": 1000, "commitment": "finalized"}
        if cursor.get("before"):
            cfg["before"] = cursor["before"]
        page = self.rpc.call("getSignaturesForAddress", [address, cfg]) or []
        keep = [s for s in page if (s.get("slot") or 0) >= self.until_slot]
        self._append("sigs.jsonl", [json.dumps({"feed": address, "tag": tag, "before": cursor.get("before"),
                                                "sigs": keep}, separators=(",", ":"))])
        if len(page) < 1000 or len(keep) < len(page):
            cursor["done"] = True
        if page:
            cursor["before"] = page[-1]["signature"]
        times = [s["blockTime"] for s in keep if s.get("blockTime")]
        if times and tag == "feed":
            st = self.state
            st["sig_earliest_bt"] = min(times + ([st["sig_earliest_bt"]] if st["sig_earliest_bt"] else []))
            st["sig_latest_bt"] = max(times + ([st["sig_latest_bt"]] if st["sig_latest_bt"] else []))
        cursor["sigs"] = cursor.get("sigs", 0) + len(keep)
        ok = [s for s in keep if s.get("err") is None]
        cursor["ok"] = cursor.get("ok", 0) + len(ok)
        return ok

    def phase_signatures(self) -> bool:
        for address, cursor in self.state["feeds"].items():
            while not cursor["done"]:
                if self.stop_requested():
                    return False
                self.page_signatures(address, cursor, "feed")
                self.count("sig_pages")
                self.save()
                self.maybe_status()
        return True

    def feed_signatures(self) -> list:
        """Successful feed signatures, newest first, deduplicated: (slot, tx_index, sig)."""
        feeds, seen, out = set(self.state["feeds"]), set(), []
        path = self.dir / "sigs.jsonl"
        if not path.exists():
            return out
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    page = json.loads(line)
                except ValueError:  # a line cut by a crash
                    continue
                if page.get("tag") != "feed" or page.get("feed") not in feeds:
                    continue
                for s in page["sigs"]:
                    if s.get("err") is None and s["signature"] not in seen:
                        seen.add(s["signature"])
                        out.append((s.get("slot") or 0, s.get("transactionIndex") or 0, s["signature"]))
        out.sort(reverse=True)
        return out

    # -- phase 2: transactions
    def process(self, sig: str) -> dict:
        """getTransaction -> swaps.jsonl. Returns the wallet's token accounts in it."""
        tx = self.rpc.call("getTransaction", [sig, {"encoding": "json", "commitment": "finalized",
                                                    # version-1 transactions exist since 2026
                                                    "maxSupportedTransactionVersion": 1}])
        kind, rows, owned = derive_swaps(tx, self.wallet)
        self.count(kind)
        if rows:
            self._append("swaps.jsonl", [json.dumps(r, separators=(",", ":")) for r in rows])
            self.count("swap_rows", len(rows))
        if tx and tx.get("blockTime"):
            bt = tx["blockTime"]
            cur = self.state["tx_earliest_bt"]
            self.state["tx_earliest_bt"] = bt if cur is None else min(cur, bt)
        if kind == "missing":
            self._append("missing.txt", [sig])
        self._append("processed.txt", [sig])
        self.processed.add(sig)
        return owned

    def expand(self, account: str) -> bool:
        """All transactions of one of the wallet's token accounts (its buys and sells of that coin)."""
        cursor = {"before": None, "done": False}
        while not cursor["done"]:
            if self.stop_requested():
                return False
            ok = self.page_signatures(account, cursor, "ata")
            self.count("ata_pages")
            for s in ok:
                if s["signature"] not in self.processed:
                    self.process(s["signature"])
                    self.maybe_status()
        self._append("atas_done.txt", [account])
        self.atas_done.add(account)
        return True

    def phase_transactions(self) -> bool:
        todo = self.feed_signatures()
        self.state["feed_ok_total"] = len(todo)
        self.log(f"{self.name}: {len(todo)} successful feed signatures, "
                 f"{sum(1 for t in todo if t[2] in self.processed)} already processed")
        for n, (_, _, sig) in enumerate(todo):
            if sig in self.processed:
                continue
            if self.stop_requested():
                return False
            owned = self.process(sig)
            self.count("feed_done")
            self.state["feed_index"] = n + 1
            if self.state["mode"] == "via":
                for account, mint in owned.items():
                    if mint != WSOL and mint not in STABLES and account not in self.atas_done:
                        if not self.expand(account):
                            return False
            self.maybe_status()
        return True

    # -- progress
    def maybe_status(self, force: bool = False) -> None:
        now = self.clock()
        if not force and now - self._last_status < self.status_every_s:
            return
        self._last_status = now
        self.save()
        if now - self._last_report >= REPORT_EVERY_S:
            self._last_report = now
            write_reports(self.dir, self.name, self.wallet, self.state)
        st, c = self.state, self.state["counts"]
        stats = self.rpc.stats if hasattr(self.rpc, "stats") else Counter()
        rate = self.rpc.rate() if hasattr(self.rpc, "rate") else 0.0
        bt = lambda t: datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if t else "-"
        eta = self.eta(rate)
        self.log(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name} {st['mode']} phase={st['phase']} "
                 f"sigs={sum(f.get('sigs', 0) for f in st['feeds'].values())} "
                 f"tx={len(self.processed)} swaps={c.get('swap_rows', 0)} nonswap={c.get('nonswap', 0)} "
                 f"missing={c.get('missing', 0)} atas={len(self.atas_done)} "
                 f"sig_earliest={bt(st['sig_earliest_bt'])}Z tx_earliest={bt(st['tx_earliest_bt'])}Z "
                 f"req={stats['requests']} rate={rate:.2f}/s 429={stats['429']} 413={stats['413']} "
                 f"5xx={stats['5xx']} eta={eta}")

    def eta(self, rate: float) -> str:
        st = self.state
        total, idx = st.get("feed_ok_total"), st.get("feed_index", 0)
        if st["phase"] != "txs" or not total or rate <= 0:
            return "?"
        done_here = self.state["counts"].get("feed_done", 0) - st.get("feed_done_at_start", 0)
        req_here = self.rpc.stats["requests"] - self._requests_at_start if hasattr(self.rpc, "stats") else 0
        per_item = req_here / done_here if done_here else 1.0
        hours = (total - idx) * per_item / rate / 3600
        return f"{hours:.1f}h"

    def run(self) -> bool:
        """Fetch until done (True) or a STOP file (False). Rebuilds trips/monthly at the end."""
        self.setup()
        try:
            if self.state["phase"] == "sigs":
                if not self.phase_signatures():
                    return False
                self.state["phase"] = "txs"
                self.save()
            self.state["feed_done_at_start"] = self.state["counts"].get("feed_done", 0)
            self._requests_at_start = getattr(self.rpc, "stats", Counter())["requests"]
            if self.state["phase"] == "txs":
                if not self.phase_transactions():
                    return False
                self.state["phase"] = "done"
            return True
        finally:
            self.maybe_status(force=True)
            self.save()
            write_reports(self.dir, self.name, self.wallet, self.state)


def load_swaps(out_dir: Path) -> list:
    path = out_dir / "swaps.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def write_reports(out_dir: Path, name: str, wallet: str, state: dict | None = None,
                  sol_usd: dict | None = None) -> dict:
    trips, bags, orphans = build_trips(load_swaps(out_dir), name)
    with open(out_dir / "trips.jsonl", "w", encoding="utf-8") as fh:
        for t in trips:
            fh.write(json.dumps(t, separators=(",", ":")) + "\n")
    state = state or {}
    summary = {
        "name": name, "wallet": wallet, "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "complete": state.get("phase") == "done", "mode": state.get("mode"),
        "sig_earliest_bt": state.get("sig_earliest_bt"), "tx_earliest_bt": state.get("tx_earliest_bt"),
        "counts": state.get("counts", {}),
        "method": "flat-to-flat round trips per mint, PnL = SOL out - SOL in (before network fees; "
                  "pnl_net_sol subtracts them), booked on the US Eastern month the trip closed; "
                  "average cost only splits open bags",
        "usd": ("pnl_usd_approx = pnl_sol x the month's SOL/USDT VWAP from Binance (UTC months): approximate"
                if sol_usd else "omitted: no SOL/USD history fetched (run --report --usd)"),
        "coverage": ("via mode: Pump.fun/PumpSwap-bought mints and all their trades on any venue; mints "
                     "traded only on other venues are missing" if state.get("mode") == "via"
                     else "every transaction that lists the wallet"),
        "months": monthly_summary(trips, bags, orphans, sol_usd),
        "open_bags": {"n": len(bags), "sol_in": round(sum(b["sol_in"] for b in bags), 6),
                      "status": "unrealized-unknown"},
        "orphan_sells": {"n": orphans["n"], "sol": round(orphans["sol"], 6)},
        "totals": {"trips": len(trips), "pnl_sol": round(sum(t["pnl_sol"] for t in trips), 6),
                   "deployed_sol": round(sum(t["sol_in"] for t in trips), 6)},
    }
    (out_dir / "monthly.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    below_normal_priority()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wallet", default="decu", help="elite name (any case) or wallet address")
    ap.add_argument("--all", action="store_true", help="every elite in turn")
    ap.add_argument("--until-slot", type=int, default=0, help="do not go older than this slot")
    ap.add_argument("--mode", choices=("auto", "wallet", "via"), default="auto")
    ap.add_argument("--rpc", default=DEFAULT_RPC, help="free public RPC endpoint")
    ap.add_argument("--rps", type=float, default=RPS)
    ap.add_argument("--report", action="store_true", help="rebuild trips/monthly from fetched swaps only")
    ap.add_argument("--usd", action="store_true", help="with --report: add approximate USD per month")
    args = ap.parse_args(argv)

    targets = [(e.name, e.wallet) for e in elite.ELITES] if args.all else [resolve(args.wallet)]
    for name, wallet in targets:
        out_dir = HISTORY_DIR / slug(name)
        out_dir.mkdir(parents=True, exist_ok=True)
        log_path = out_dir / "fetch.log"

        def log(msg, _path=log_path):
            print(msg, flush=True)
            with open(_path, "a", encoding="utf-8") as fh:
                fh.write(msg + "\n")

        if args.report:
            state_path = out_dir / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
            s = write_reports(out_dir, name, wallet, state, month_sol_usd() if args.usd else None)
            print(f"{name}: {s['totals']}")
            continue
        rpc = PacedRpc(args.rpc, args.rps, log=log)
        fetcher = Fetcher(name, wallet, rpc, out_dir, args.mode, args.until_slot, log=log)
        log(f"== {name} {wallet} start {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
            f"rpc={args.rpc} rps={args.rps}")
        finished = fetcher.run()
        log(f"== {name} {'finished' if finished else 'stopped'}")
        if not finished:
            try:
                (out_dir / "STOP").unlink()
            except OSError:
                pass
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
