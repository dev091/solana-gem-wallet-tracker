"""Rolling per-coin state built only from events already received.

Every field is updated in arrival order, so a strategy reading it at time `now`
sees nothing it could not have known then (no future highs, no eventual winners).
Holder figures are approximate: they cover only trades seen since the coin was first
seen by this process (exact for coins whose creation we saw).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .chain_events import PUMP_SUPPLY, WSOL

WINDOW_MS = 600_000       # keep 10 minutes of individual trades per coin
MAX_HOLDERS = 5_000


@dataclass
class Trade:
    rx: int
    side: str
    sol: float
    tokens: float
    user: str
    price: float


@dataclass
class TokenState:
    mint: str
    first_rx: int
    venue: str = ""
    created_ts: int = 0          # chain time of creation, 0 if creation not seen
    seen_create: bool = False
    creator: str = ""
    name: str = ""
    symbol: str = ""
    supply: float = PUMP_SUPPLY
    mayhem: bool = False
    pool: str = ""
    migrated: bool = False
    price: float = 0.0           # SOL per whole token after the last trade
    quote_mint: str = WSOL       # non-WSOL: reserves and price are in that token, not SOL
    progress: float = 0.0
    reserve_quote: int = 0
    reserve_base: int = 0
    fee_bps: int = 0
    last_rx: int = 0
    last_ts: int = 0
    ath_mcap: float = 0.0        # SOL
    ath_rx: int = 0
    n_buys: int = 0
    n_sells: int = 0
    buy_sol: float = 0.0
    sell_sol: float = 0.0
    dev_bought: float = 0.0      # tokens
    dev_sold: float = 0.0
    trades: deque = field(default_factory=deque)
    holders: dict = field(default_factory=dict)   # user -> net tokens seen
    elite_buys: list = field(default_factory=list)  # (rx, name, sol)
    elite_sells: list = field(default_factory=list)
    _wcache: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def mcap(self) -> float:
        """Market cap in SOL."""
        return self.price * self.supply

    def age_s(self, now_ms: int) -> float:
        if self.created_ts:
            return max(0.0, now_ms / 1000 - self.created_ts)
        return (now_ms - self.first_rx) / 1000

    def window(self, now_ms: int, secs: float) -> dict:
        """Flow over the last `secs` seconds (cached: many algos ask the same window per event)."""
        key = (now_ms, secs, len(self.trades), self.trades[-1].rx if self.trades else 0, self.price)
        hit = self._wcache.get(key)
        if hit is not None:
            return dict(hit)
        if len(self._wcache) > 16:
            self._wcache.clear()
        cut = now_ms - secs * 1000
        buys = sells = 0
        bsol = ssol = 0.0
        buyers = set()
        first_price = None
        for t in reversed(self.trades):  # kept sorted by rx, so stop at the first older trade
            if t.rx < cut:
                break
            first_price = t.price
            if t.side == "buy":
                buys += 1
                bsol += t.sol
                buyers.add(t.user)
            else:
                sells += 1
                ssol += t.sol
        change = (self.price / first_price - 1) if first_price else 0.0
        out = {"buys": buys, "sells": sells, "buy_sol": bsol, "sell_sol": ssol,
               "net_sol": bsol - ssol, "unique_buyers": len(buyers), "price_change": change}
        self._wcache[key] = out
        return dict(out)

    def holder_count(self) -> int:
        return sum(1 for v in self.holders.values() if v > 0)

    def top_holder_share(self, n: int = 10) -> float:
        """Share of supply held by the top `n` wallets seen (curve itself excluded)."""
        pos = sorted((v for v in self.holders.values() if v > 0), reverse=True)[:n]
        return sum(pos) / self.supply if self.supply else 0.0


class Market:
    def __init__(self):
        self.tokens: dict[str, TokenState] = {}
        self.pool_mint: dict[str, str] = {}
        self.elite_names: dict[str, str] = {}
        self.venue_fee: dict[str, int] = {"pump": 125}  # latest total fee seen per venue

    def get(self, mint: str) -> TokenState | None:
        return self.tokens.get(mint)

    def _token(self, mint: str, rx: int) -> TokenState:
        st = self.tokens.get(mint)
        if st is None:
            st = self.tokens[mint] = TokenState(mint=mint, first_rx=rx)
        return st

    def apply(self, ev, rx: int) -> TokenState | None:
        """Fold one ChainEvent (mint already resolved) into the coin's state."""
        mint = ev.mint or self.pool_mint.get(ev.pool, "")
        if not mint:
            return None
        st = self._token(mint, rx)
        if ev.kind == "create":
            st.seen_create = True
            st.created_ts = ev.ts or rx // 1000
            st.creator = ev.extra.get("creator") or ev.user
            st.name, st.symbol = ev.extra.get("name", ""), ev.extra.get("symbol", "")
            st.supply = ev.extra.get("supply") or st.supply
            st.mayhem = bool(ev.extra.get("mayhem"))
            st.venue = ev.venue
            if ev.price and not st.last_rx:  # the dev's first buy may have arrived already
                st.price = ev.price
                st.reserve_quote, st.reserve_base = ev.reserve_quote, ev.reserve_base
                st.fee_bps = self.venue_fee.get(ev.venue, 0)
            return st
        if ev.kind == "migrate":
            st.migrated, st.progress = True, 1.0
            return st
        if ev.kind == "pool":
            st.pool, st.migrated, st.venue = ev.pool, True, ev.venue
            self.pool_mint[ev.pool] = mint
            return st
        if ev.kind != "trade":
            return st
        st.venue = ev.venue
        st.quote_mint = getattr(ev, "quote_mint", "") or WSOL
        if ev.pool:
            st.pool = ev.pool
        if ev.venue == "pumpswap":
            st.migrated = True
        if not st.creator and ev.extra.get("creator"):
            st.creator = ev.extra["creator"]
        st.price, st.progress = ev.price, ev.progress
        st.reserve_quote, st.reserve_base, st.fee_bps = ev.reserve_quote, ev.reserve_base, ev.fee_bps
        self.venue_fee[ev.venue] = ev.fee_bps
        st.last_rx, st.last_ts = rx, ev.ts or st.last_ts
        if st.mcap > st.ath_mcap:
            st.ath_mcap, st.ath_rx = st.mcap, rx
        sol = ev.quote / 1e9
        tokens = ev.tokens / 1e6
        buy = ev.side == "buy"
        if buy:
            st.n_buys += 1
            st.buy_sol += sol
        else:
            st.n_sells += 1
            st.sell_sol += sol
        if ev.user:
            if ev.user in st.holders or len(st.holders) < MAX_HOLDERS:
                st.holders[ev.user] = st.holders.get(ev.user, 0.0) + (tokens if buy else -tokens)
            if ev.user == st.creator:
                if buy:
                    st.dev_bought += tokens
                else:
                    st.dev_sold += tokens
            name = self.elite_names.get(ev.user)
            if name:
                (st.elite_buys if buy else st.elite_sells).append((rx, name, sol))
        trade = Trade(rx, ev.side, sol, tokens, ev.user, ev.price)
        if st.trades and rx < st.trades[-1].rx:  # a late (parked) event: keep rx order
            i = len(st.trades)
            while i and st.trades[i - 1].rx > rx:
                i -= 1
            st.trades.insert(i, trade)
        else:
            st.trades.append(trade)
        while st.trades and st.trades[0].rx < rx - WINDOW_MS:
            st.trades.popleft()
        return st

    def prune(self, now_ms: int, keep: set, idle_ms: int = 1_800_000) -> int:
        """Forget coins idle for `idle_ms` unless listed in `keep` (open positions)."""
        stale = [m for m, st in self.tokens.items()
                 if m not in keep and max(st.last_rx, st.first_rx) < now_ms - idle_ms]
        for m in stale:
            del self.tokens[m]
        return len(stale)
