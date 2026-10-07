"""Live tracking: notice what tracked wallets buy and sell, alert, and paper-trade the copy.

Two ways to notice trades:
  holdings (default) - compare each wallet's token holdings with the last check: 2 RPC calls per
                       wallet no matter how much it trades, so the free public RPC copes
  txs                - read every new transaction: exact sizes and links, but needs a fast RPC
"""
from __future__ import annotations

import time

from . import alerts, config, util
from .config import IGNORED_MINTS, SOL_MINT, STABLES
from .paper import PaperBook
from .prices import SolPrice, token_quotes
from .solana import SolanaRpc, delta_from_rpc_tx
from .trades import trade_events

STATE_FILE = config.DATA_DIR / "watch_state.json"
HOLDINGS_FILE = config.DATA_DIR / "watch_holdings.json"
ACTIVITY_FILE = config.DOCS_DATA_DIR / "activity.json"
LEADERBOARD_FILE = config.DOCS_DATA_DIR / "leaderboard.json"
FEED_LIMIT = 300
CONSENSUS_WINDOW = 24 * 3600   # several tracked wallets buying the same coin within a day
MAX_NEW_TXS = 100              # txs mode: per wallet per check
MIN_EVENT_USD = 25.0           # holdings mode: ignore dust moves
MIN_LIQUIDITY_USD = 5_000.0    # coins with less are spam airdrops or dead
TOKEN_PROGRAMS = ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",   # SPL Token
                  "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")   # Token-2022 (newer Pump.fun coins)
NOT_TRADES = set(STABLES) | set(IGNORED_MINTS) | {SOL_MINT}


def tracked_wallets(tiers=("STRICT", "GEM_HUNTER"), board: int = 15) -> list:
    """Wallets that passed the last scan, wallets/watchlist.txt, and the most consistent
    leaderboard wallets (tier BOARD) from the last `board` snapshot."""
    out, seen = [], set()

    def add(wallet, label, tier, gems=0):
        if util.is_address(wallet) and wallet not in seen:
            seen.add(wallet)
            out.append({"wallet": wallet, "label": label, "tier": tier, "gems": gems})

    for row in util.load_json(config.DATA_DIR / "tracked.json", {}).get("wallets") or []:
        if row.get("tier") in tiers:
            add(row.get("wallet"), row.get("label") or "", row["tier"], row.get("gems") or 0)
    for wallet, label in util.read_wallet_list(config.WATCHLIST_FILE):
        add(wallet, label or "watchlist", "WATCHLIST")
    if board > 0:
        boards = util.load_json(LEADERBOARD_FILE, {})
        for r in (boards.get("repeat_leaders") or [])[:board]:
            add(r["wallet"], " ".join(f"consistent {r.get('name') or ''} (score {r['score']})".split()), "BOARD")
        for r in (boards.get("efficient_winners") or [])[:max(board // 2, 1)]:
            add(r["wallet"], f"small-money winner {r.get('name') or ''}".strip(), "BOARD")
    return out


def fetch_holdings(rpc, wallet: str) -> dict:
    """{mint: token amount} the wallet holds right now (both token programs)."""
    held: dict = {}
    for program in TOKEN_PROGRAMS:
        reply = rpc.call("getTokenAccountsByOwner",
                         [wallet, {"programId": program}, {"encoding": "jsonParsed", "commitment": "confirmed"}])
        for acct in (reply or {}).get("value") or []:
            info = (((acct.get("account") or {}).get("data") or {}).get("parsed") or {}).get("info") or {}
            mint, amount = info.get("mint"), info.get("tokenAmount") or {}
            if not mint or mint in NOT_TRADES:
                continue
            ui = util.num(amount.get("amount")) / 10 ** int(util.num(amount.get("decimals")))
            if ui > 0:
                held[mint] = held.get(mint, 0.0) + ui
    return held


class Watcher:
    def __init__(self, rpc: SolanaRpc, sol: SolPrice, include_sells: bool = False, log=print,
                 mode: str = "holdings", alert_tiers=("STRICT", "GEM_HUNTER", "WATCHLIST"),
                 paper: PaperBook | None = None):
        self.rpc, self.sol, self.include_sells, self.log = rpc, sol, include_sells, log
        self.mode, self.alert_tiers = mode, set(alert_tiers)
        self.paper = paper if paper is not None else PaperBook()
        self.state = util.load_json(STATE_FILE, {})
        for key in ("last_sig", "recent_buys", "consensus_alerted"):
            self.state.setdefault(key, {})
        self.holdings = util.load_json(HOLDINGS_FILE, {}) if mode == "holdings" else {}
        activity = util.load_json(ACTIVITY_FILE, {})
        self.feed = activity.get("events") or []
        self.consensus = activity.get("consensus") or []

    # ------------------------------------------------------------- noticing trades
    def poll_wallet(self, info: dict) -> list:
        return self._poll_holdings(info) if self.mode == "holdings" else self._poll_txs(info)

    @staticmethod
    def _base_event(info: dict, side: str, mint: str, tokens: float, ts: int) -> dict:
        return {"ts": ts, "wallet": info["wallet"], "label": info.get("label") or "",
                "tier": info.get("tier") or "", "gems": info.get("gems") or 0,
                "side": side, "mint": mint, "tokens": tokens}

    def _poll_holdings(self, info: dict) -> list:
        wallet = info["wallet"]
        now_held = fetch_holdings(self.rpc, wallet)
        before = self.holdings.get(wallet)
        self.holdings[wallet] = now_held
        if before is None:
            return []  # first look at this wallet: baseline only, no backlog alerts
        ts, events = util.now(), []
        for mint, amount in now_held.items():
            was = before.get(mint, 0.0)
            if amount > was * 1.001:
                events.append(self._base_event(info, "buy", mint, amount - was, ts))
        for mint, was in before.items():
            amount = now_held.get(mint, 0.0)
            if amount < was * 0.5:
                events.append(self._base_event(info, "sell", mint, was - amount, ts))
        return events

    def _poll_txs(self, info: dict) -> list:
        wallet = info["wallet"]
        last = self.state["last_sig"].get(wallet)
        infos, complete = self.rpc.signatures(wallet, max_count=MAX_NEW_TXS if last else 1, until=last)
        if not infos:
            return []
        self.state["last_sig"][wallet] = infos[0]["signature"]
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
                if ev.kind in ("buy", "sell"):
                    event = self._base_event(info, ev.kind, ev.mint, ev.amount, ev.ts or util.now())
                    sol_price = self.sol.at(ev.ts)
                    event.update(usd=round(ev.usd, 2), signature=ev.signature,
                                 sol=round(ev.usd / sol_price, 4) if sol_price else None,
                                 via_fomo=delta.fee_payer == config.FOMO_SIGNER)
                    events.append(event)
        return events

    # ------------------------------------------------------------- one round
    def run_once(self, wallets: list) -> list:
        raw = []
        for info in wallets:
            try:
                raw += self.poll_wallet(info)
            except Exception as exc:
                self.log(f"   {util.short(info['wallet'])}: {exc}")
        mints = {e["mint"] for e in raw} | {p["mint"] for p in self.paper.open_positions}
        quotes = token_quotes(sorted(mints), log=self.log) if mints else {}

        new = []
        for e in raw:
            q = quotes.get(e["mint"])
            price = q.price if q else None
            if e.get("usd") is None:  # holdings mode: size it at today's price
                e["usd"] = round(e["tokens"] * price, 2) if price else None
            liquidity = q.liquidity if q else None
            if price is None or (liquidity is not None and liquidity < MIN_LIQUIDITY_USD) \
                    or (e["usd"] or 0) < MIN_EVENT_USD:
                continue  # spam airdrop, dead coin or dust
            e.update(symbol=(q.symbol if q else "") or util.short(e["mint"]), price=price,
                     market_cap=q.market_cap if q else None, liquidity=liquidity)
            new.append(e)
        new.sort(key=lambda e: e["ts"])

        now = util.now()
        for e in new:
            if e["side"] == "buy":
                self.paper.on_buy(e, now)
            else:
                self.paper.on_sell(e["wallet"], e["mint"], e["price"], now)
            self.log(f"   {e['side'].upper():4} {e['symbol']:<12} {util.usd(e['usd']):>8}  "
                     f"by {util.short(e['wallet'])} ({e['tier']})")
            wanted = e["side"] == "buy" or self.include_sells
            if wanted and e["tier"] in self.alert_tiers and alerts.enabled():
                alerts.send(trade_alert(e), self.log)
        self.paper.mark({m: (q.price or 0.0) for m, q in quotes.items()}, now)
        self.feed = (list(reversed(new)) + self.feed)[:FEED_LIMIT]

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
        symbols = {e["mint"]: e.get("symbol") for e in self.feed + new}
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
            util.save_json(ACTIVITY_FILE, {"updated_at": util.now(), "mode": self.mode, "tracked": wallets,
                                           "events": self.feed, "consensus": self.consensus},
                           js_var="GEM_ACTIVITY")
        util.save_json(STATE_FILE, self.state)
        if self.mode == "holdings":
            util.save_json(HOLDINGS_FILE, self.holdings)
        self.paper.save(util.now())


def trade_alert(e: dict) -> list:
    side = "🟢 BUY" if e["side"] == "buy" else "🔴 SELL"
    sol = f" ({e['sol']} SOL)" if e.get("sol") else ""
    via = " via Fomo app" if e.get("via_fomo") else ""
    market = []
    if e.get("market_cap"):
        market.append(f"MC {util.usd(e['market_cap'])}")
    if e.get("liquidity") is not None:
        market.append(f"Liq {util.usd(e['liquidity'])}")
    who = " · ".join(x for x in (e.get("tier"), f"{e['gems']} gems" if e.get("gems") else "",
                                 e.get("label")) if x)
    lines = [
        (f"{side} {e['symbol']} — {util.usd(e['usd'])}{sol}{via}", None),
        (f"Wallet {util.short(e['wallet'])} ({who})", f"https://gmgn.ai/sol/address/{e['wallet']}"),
        (" · ".join(market) or "no market data yet", None),
        ("Chart (DexScreener)", f"https://dexscreener.com/solana/{e['mint']}"),
    ]
    if e.get("signature"):
        lines.append(("Transaction (Solscan)", f"https://solscan.io/tx/{e['signature']}"))
    return lines


def consensus_alert(item: dict) -> list:
    return [
        (f"🔥 {len(item['wallets'])} tracked wallets bought {item['symbol']} in the last 24h", None),
        ("Chart (DexScreener)", f"https://dexscreener.com/solana/{item['mint']}"),
        *[(f"• {util.short(w)}", f"https://gmgn.ai/sol/address/{w}") for w in item["wallets"]],
    ]


def run(loop: bool = False, interval: float = 30.0, include_sells: bool = False,
        tiers=("STRICT", "GEM_HUNTER"), board: int = 15, mode: str = "holdings", log=print) -> int:
    watcher = Watcher(SolanaRpc(config.rpc_url()), SolPrice(), include_sells, log, mode=mode)
    while True:
        wallets = tracked_wallets(tiers, board)  # re-read each round so a new scan is picked up
        if not wallets:
            log("No wallets to track yet: run `board` or a scan first, or add wallets/watchlist.txt")
            return 0
        log(f"Checking {len(wallets)} wallet(s) [{mode} mode]…")
        new = watcher.run_once(wallets)
        summary = watcher.paper.summary()["overall"]
        log(f"{len(new)} new trade(s); paper trading: {len(watcher.paper.open_positions)} open, "
            f"{summary['trades']} closed, mirror PnL {util.usd(summary['mirror']['pnl_usd'])}"
            + ("" if alerts.enabled() else "  (alerts off: set TELEGRAM_* or DISCORD_WEBHOOK_URL)"))
        if not loop:
            return 0
        time.sleep(interval)
