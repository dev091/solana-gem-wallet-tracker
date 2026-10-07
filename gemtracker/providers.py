"""Where a wallet's per-coin positions come from.

* RpcProvider          - free, no key: reads raw transactions from a Solana RPC and
                         computes everything itself (slow on the public RPC, fast with Helius).
* SolanaTrackerProvider - SOLANATRACKER_API_KEY: ready-made per-coin PnL, a few requests per wallet.
"""
from __future__ import annotations

from . import config, net, util
from .criteria import WalletReport
from .prices import SolPrice, token_quotes
from .solana import HeliusHistory, SolanaRpc, fetch_history
from .trades import Position, apply_quotes, build_positions


class ProviderError(Exception):
    pass


class RpcProvider:
    name = "rpc"

    def __init__(self, max_txs: int = 3000, workers: int = 6, log=print):
        self.max_txs = max_txs
        self.workers = workers
        self.log = log
        self.rpc = SolanaRpc(config.rpc_url())
        key = config.env("HELIUS_API_KEY")
        self.helius = HeliusHistory(key) if key else None
        self.sol = SolPrice()

    def describe(self) -> str:
        if self.helius:
            return "Solana RPC + Helius parsed history"
        if "api.mainnet-beta.solana.com" in self.rpc.url:
            return "free public Solana RPC (slow; set HELIUS_API_KEY for ~50x speed)"
        return f"Solana RPC ({net.redact(self.rpc.url)})"

    def report(self, wallet: str) -> WalletReport:
        history = fetch_history(wallet, self.rpc, self.helius, self.max_txs, self.workers, self.log)
        if not history.complete:
            return WalletReport(wallet, [], history_complete=False, too_active=True,
                                tx_count=history.tx_count, source=history.source)
        positions = build_positions(history.deltas, self.sol.at)
        traded = [p.mint for p in positions if p.cost_usd > 0 or p.balance > 0]
        apply_quotes(positions, token_quotes(traded, log=self.log))
        notes = []
        via_fomo = sum(1 for d in history.deltas if d.fee_payer == config.FOMO_SIGNER and d.tokens)
        if via_fomo:
            notes.append(f"{via_fomo} trade(s) placed through the Fomo app")
        return WalletReport(wallet, positions, tx_count=history.tx_count, source=history.source, notes=notes)


def position_from_solanatracker(row: dict) -> Position:
    """Map a Solana Tracker PnL-v2 position onto our Position."""
    current = row.get("current") or {}
    volume = row.get("volume") or {}
    counts = row.get("counts") or {}
    timing = row.get("timing") or {}
    meta = row.get("meta") or {}
    pos = Position(row.get("token") or "")
    pos.symbol = meta.get("symbol") or ""
    pos.cost_usd = util.num(row.get("invested") if row.get("invested") is not None else volume.get("buyUsd"))
    pos.proceeds_usd = util.num(row.get("proceeds") if row.get("proceeds") is not None else volume.get("sellUsd"))
    pos.value_usd = util.num(current.get("value"))
    pos.balance = util.num(current.get("balance"))
    pos.bought = util.num(volume.get("tokensBought"))
    pos.sold = util.num(volume.get("tokensSold"))
    pos.buys = int(util.num(counts.get("buys")))
    pos.sells = int(util.num(counts.get("sells")))
    pos.first_buy_ts = util.to_seconds(timing.get("firstBuy")) or 0
    pos.last_trade_ts = util.to_seconds(timing.get("lastTrade")) or 0
    pos.price_usd = current.get("price") if current.get("price") is not None else meta.get("price")
    pos.liquidity_usd = meta.get("liquidity")
    if pos.sold > pos.bought * 1.02 and pos.bought >= 0:
        pos.transfer_in = pos.sold - pos.bought
        pos.flag("sold more than it bought (received coins by transfer)")
    return pos


class SolanaTrackerProvider:
    name = "solanatracker"
    BASE = "https://data.solanatracker.io"

    def __init__(self, api_key: str, max_tokens: int = 300, log=print):
        if not api_key:
            raise ProviderError("SOLANATRACKER_API_KEY is not set")
        self.key = api_key
        self.max_tokens = max_tokens
        self.log = log
        net.set_rate("data.solanatracker.io", 4)

    def describe(self) -> str:
        return "Solana Tracker PnL API"

    def get(self, path: str, params: dict | None = None):
        return net.get_json(self.BASE + path, params=params, headers={"x-api-key": self.key})

    def prescreen(self, wallets: list) -> dict:
        """One batch call per 100 wallets; returns {wallet: reason} for obvious bots."""
        skip = {}
        for chunk in util.chunks(wallets, 100):
            try:
                data = net.post_json(self.BASE + "/v2/pnl/wallets/batch", {"wallets": chunk},
                                     headers={"x-api-key": self.key})
            except Exception as exc:
                self.log(f"   batch pre-screen skipped ({exc})")
                return skip
            for row in (data or {}).get("wallets") or []:
                tags = row.get("tags") or {}
                tokens = util.num(((row.get("summary") or {}).get("counts") or {}).get("tokensTraded"))
                if tags.get("isArbitrage"):
                    skip[row.get("wallet")] = "arbitrage bot"
                elif tokens > self.max_tokens:
                    skip[row.get("wallet")] = f"traded {int(tokens):,} coins: bot / scalper"
        return skip

    def report(self, wallet: str) -> WalletReport:
        positions, identity, cursor = [], None, None
        while True:
            data = self.get(f"/v2/pnl/wallets/{wallet}/positions",
                            {"filter": "all", "sort": "last_trade", "direction": "desc",
                             "limit": 100, "cursor": cursor}) or {}
            if data.get("queued") or data.get("indexed") is False:
                return WalletReport(wallet, [], history_complete=False, source=self.name,
                                    notes=["Solana Tracker is still indexing this wallet; scan again later"])
            identity = identity or data.get("identity")
            positions += [position_from_solanatracker(row) for row in data.get("positions") or []]
            page = data.get("pagination") or {}
            if len([p for p in positions if p.cost_usd > 0]) > self.max_tokens:
                return WalletReport(wallet, positions, history_complete=False, too_active=True,
                                    tx_count=sum(p.buys + p.sells for p in positions),
                                    source=self.name, identity=identity)
            cursor = page.get("nextCursor")
            if not page.get("hasMore") or not cursor:
                break
        return WalletReport(wallet, positions, source=self.name, identity=identity,
                            tx_count=sum(p.buys + p.sells for p in positions))


def make_provider(name: str = "auto", *, max_txs: int = 3000, workers: int = 6,
                  max_tokens: int = 300, log=print):
    key = config.env("SOLANATRACKER_API_KEY")
    if name == "solanatracker" or (name == "auto" and key):
        return SolanaTrackerProvider(key, max_tokens=max_tokens, log=log)
    if name in ("auto", "rpc"):
        return RpcProvider(max_txs=max_txs, workers=workers, log=log)
    raise ProviderError(f"unknown provider {name!r} (use auto, rpc or solanatracker)")
