"""Live tracking: alert when a tracked gem hunter buys (or sells) a coin."""
from __future__ import annotations

import time

from . import alerts, config, util
from .prices import SolPrice, token_quotes
from .solana import SolanaRpc, delta_from_rpc_tx
from .trades import trade_events

STATE_FILE = config.DATA_DIR / "watch_state.json"
ACTIVITY_FILE = config.DOCS_DATA_DIR / "activity.json"
FEED_LIMIT = 300
CONSENSUS_WINDOW = 24 * 3600   # several tracked wallets buying the same coin within a day
MAX_NEW_TXS = 100              # per wallet per poll


def tracked_wallets(tiers=("STRICT", "GEM_HUNTER")) -> list:
    """Wallets that passed the last scan, plus everything in wallets/watchlist.txt."""
    out, seen = [], set()
    data = util.load_json(config.DATA_DIR / "tracked.json", {})
    for row in data.get("wallets") or []:
        wallet = row.get("wallet")
        if row.get("tier") in tiers and util.is_address(wallet) and wallet not in seen:
            seen.add(wallet)
            out.append({"wallet": wallet, "label": row.get("label") or "", "tier": row["tier"],
                        "gems": row.get("gems") or 0})
    for wallet, label in util.read_wallet_list(config.WATCHLIST_FILE):
        if wallet not in seen:
            seen.add(wallet)
            out.append({"wallet": wallet, "label": label or "watchlist", "tier": "WATCHLIST", "gems": 0})
    return out


class Watcher:
    def __init__(self, rpc: SolanaRpc, sol: SolPrice, include_sells: bool = False, log=print):
        self.rpc, self.sol, self.include_sells, self.log = rpc, sol, include_sells, log
        self.state = util.load_json(STATE_FILE, {})
        for key in ("last_sig", "recent_buys", "consensus_alerted"):
            self.state.setdefault(key, {})
        activity = util.load_json(ACTIVITY_FILE, {})
        self.feed = activity.get("events") or []
        self.consensus = activity.get("consensus") or []

    def poll_wallet(self, info: dict) -> list:
        wallet = info["wallet"]
        last = self.state["last_sig"].get(wallet)
        infos, complete = self.rpc.signatures(wallet, max_count=MAX_NEW_TXS if last else 1, until=last)
        if not infos:
            return []
        newest = infos[0]["signature"]
        self.state["last_sig"][wallet] = newest
        if last is None:
            return []  # first look at this wallet: start tracking from now, no backlog alerts
        if not complete:
            self.log(f"   {util.short(wallet)}: >{MAX_NEW_TXS} new transactions, only the newest checked")
        signatures = [i["signature"] for i in reversed(infos) if i.get("err") is None]
        events = []
        for tx in self.rpc.transactions(signatures, workers=4) if signatures else []:
            delta = delta_from_rpc_tx(tx, wallet)
            if not delta:
                continue
            for ev in trade_events(delta, self.sol.at):
                if ev.kind == "buy" or (self.include_sells and ev.kind == "sell"):
                    sol_price = self.sol.at(ev.ts)
                    events.append({
                        "ts": ev.ts or util.now(), "wallet": wallet, "label": info.get("label") or "",
                        "tier": info.get("tier") or "", "gems": info.get("gems") or 0,
                        "side": ev.kind, "mint": ev.mint, "tokens": ev.amount,
                        "usd": round(ev.usd, 2), "sol": round(ev.usd / sol_price, 4) if sol_price else None,
                        "signature": ev.signature,
                    })
        return events

    def run_once(self, wallets: list) -> list:
        new = []
        for info in wallets:
            try:
                new += self.poll_wallet(info)
            except Exception as exc:
                self.log(f"   {util.short(info['wallet'])}: {exc}")
        if new:
            quotes = token_quotes([e["mint"] for e in new], log=self.log)
            for e in new:
                q = quotes.get(e["mint"])
                e.update(symbol=(q.symbol if q else "") or util.short(e["mint"]),
                         price=q.price if q else None,
                         market_cap=q.market_cap if q else None,
                         liquidity=q.liquidity if q else None)
            new.sort(key=lambda e: e["ts"])
            self.feed = (list(reversed(new)) + self.feed)[:FEED_LIMIT]
            for e in new:
                self.log(f"   {e['side'].upper():4} {e['symbol']:<12} {util.usd(e['usd']):>8}  "
                         f"by {util.short(e['wallet'])} ({e['tier']})")
                if alerts.enabled():
                    alerts.send(trade_alert(e), self.log)
        before = [c["mint"] for c in self.consensus]
        self._update_consensus(new)
        self.save(wallets, changed=bool(new) or before != [c["mint"] for c in self.consensus])
        return new

    def _update_consensus(self, new: list) -> None:
        now = util.now()
        recent = self.state["recent_buys"]
        for e in new:
            if e["side"] == "buy":
                recent.setdefault(e["mint"], {})[e["wallet"]] = e["ts"]
        cutoff = now - CONSENSUS_WINDOW
        for mint in list(recent):
            recent[mint] = {w: ts for w, ts in recent[mint].items() if ts >= cutoff}
            if not recent[mint]:
                del recent[mint]
        symbols = {e["mint"]: e.get("symbol") for e in self.feed}
        self.consensus = []
        for mint, buyers in recent.items():
            if len(buyers) < 2:
                continue
            item = {"mint": mint, "symbol": symbols.get(mint) or util.short(mint),
                    "wallets": sorted(buyers), "last_ts": max(buyers.values())}
            self.consensus.append(item)
            if self.state["consensus_alerted"].get(mint, 0) < cutoff and alerts.enabled():
                alerts.send(consensus_alert(item), self.log)
                self.state["consensus_alerted"][mint] = now
        self.state["consensus_alerted"] = {m: ts for m, ts in self.state["consensus_alerted"].items()
                                           if ts >= cutoff}

    def save(self, wallets: list, changed: bool) -> None:
        """State every round; the dashboard feed only when something changed (keeps git history quiet)."""
        tracked = [w["wallet"] for w in wallets]
        if changed or not ACTIVITY_FILE.exists() or self.state.get("tracked") != tracked:
            self.state["tracked"] = tracked
            util.save_json(ACTIVITY_FILE, {"updated_at": util.now(), "tracked": wallets, "events": self.feed,
                                           "consensus": self.consensus}, js_var="GEM_ACTIVITY")
        util.save_json(STATE_FILE, self.state)


def trade_alert(e: dict) -> list:
    side = "🟢 BUY" if e["side"] == "buy" else "🔴 SELL"
    sol = f" ({e['sol']} SOL)" if e.get("sol") else ""
    market = []
    if e.get("market_cap"):
        market.append(f"MC {util.usd(e['market_cap'])}")
    if e.get("liquidity") is not None:
        market.append(f"Liq {util.usd(e['liquidity'])}")
    who = " · ".join(x for x in (e.get("tier"), f"{e['gems']} gems" if e.get("gems") else "",
                                 e.get("label")) if x)
    return [
        (f"{side} {e['symbol']} — {util.usd(e['usd'])}{sol}", None),
        (f"Wallet {util.short(e['wallet'])} ({who})", f"https://gmgn.ai/sol/address/{e['wallet']}"),
        (" · ".join(market) or "no market data yet", None),
        ("Chart (DexScreener)", f"https://dexscreener.com/solana/{e['mint']}"),
        ("Transaction (Solscan)", f"https://solscan.io/tx/{e['signature']}"),
    ]


def consensus_alert(item: dict) -> list:
    return [
        (f"🔥 {len(item['wallets'])} tracked gem hunters bought {item['symbol']} in the last 24h", None),
        ("Chart (DexScreener)", f"https://dexscreener.com/solana/{item['mint']}"),
        *[(f"• {util.short(w)}", f"https://gmgn.ai/sol/address/{w}") for w in item["wallets"]],
    ]


def run(loop: bool = False, interval: float = 30.0, include_sells: bool = False,
        tiers=("STRICT", "GEM_HUNTER"), log=print) -> int:
    watcher = Watcher(SolanaRpc(config.rpc_url()), SolPrice(), include_sells, log)
    while True:
        wallets = tracked_wallets(tiers)  # re-read each round so a new scan is picked up
        if not wallets:
            log("No wallets to track yet: run a scan first, or add addresses to wallets/watchlist.txt")
            return 0
        log(f"Checking {len(wallets)} wallet(s)…")
        new = watcher.run_once(wallets)
        log(f"{len(new)} new trade(s)" + ("" if alerts.enabled() else
                                          "  (alerts off: set TELEGRAM_* or DISCORD_WEBHOOK_URL)"))
        if not loop:
            return 0
        time.sleep(interval)
