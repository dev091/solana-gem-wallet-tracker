"""Turn balance changes into trades and per-coin positions (money in vs money out)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import IGNORED_MINTS, STABLES

# Flows smaller than this are fees / account rent, not a real buy or sell.
DUST_USD = 1.0


@dataclass
class Event:
    kind: str        # buy | sell | transfer_in | transfer_out
    mint: str
    amount: float    # tokens
    usd: float       # paid (buy) or received (sell); 0 for transfers
    ts: int
    signature: str
    note: str = ""


def trade_events(delta, sol_usd, dust_usd: float = DUST_USD) -> list:
    """Classify one transaction's balance changes into buy / sell / transfer events.

    A coin going up while SOL/stables go down is a buy; a coin going down while
    SOL/stables come in is a sell.  Coins moving with no money flow are transfers
    (airdrops, moves between a trader's own wallets).
    """
    moved = {m: a for m, a in delta.tokens.items() if a and m not in STABLES and m not in IGNORED_MINTS}
    if not moved:
        return []
    cash_usd = sum(delta.tokens.get(m, 0.0) for m in STABLES)
    if delta.sol:
        cash_usd += delta.sol * sol_usd(delta.ts)

    got = {m: a for m, a in moved.items() if a > 0}
    gave = {m: -a for m, a in moved.items() if a < 0}
    note = "token-for-token swap" if got and gave else ""
    events = []
    if got:
        paid = cash_usd < -dust_usd
        share = -cash_usd / len(got) if paid else 0.0
        for mint, amount in got.items():
            events.append(Event("buy" if paid else "transfer_in", mint, amount, share,
                                delta.ts, delta.signature, note))
    if gave:
        received = cash_usd > dust_usd
        share = cash_usd / len(gave) if received else 0.0
        for mint, amount in gave.items():
            events.append(Event("sell" if received else "transfer_out", mint, amount, share,
                                delta.ts, delta.signature, note))
    return events


@dataclass
class Position:
    """Everything one wallet did with one coin."""

    mint: str
    symbol: str = ""
    cost_usd: float = 0.0        # USD spent buying
    proceeds_usd: float = 0.0    # USD received selling
    value_usd: float = 0.0       # what is still held, at today's price (0 if dead / no liquidity)
    balance: float = 0.0         # tokens still held
    bought: float = 0.0
    sold: float = 0.0
    transfer_in: float = 0.0     # tokens received without paying
    transfer_out: float = 0.0    # tokens sent away without selling
    buys: int = 0
    sells: int = 0
    first_buy_ts: int = 0
    last_trade_ts: int = 0
    first_buy_sig: str = ""
    price_usd: float | None = None
    liquidity_usd: float | None = None
    launched_ts: int | None = None
    verified: bool | None = None  # on Jupiter's verified list (None = unknown)
    flags: list = field(default_factory=list)

    @property
    def realized_usd(self) -> float:
        """Cash out minus cash in."""
        return self.proceeds_usd - self.cost_usd

    @property
    def total_usd(self) -> float:
        """Cash out plus what is still held, minus cash in."""
        return self.proceeds_usd + self.value_usd - self.cost_usd

    @property
    def multiple(self) -> float | None:
        """How many x the entry became (sold + still held) / paid."""
        if self.cost_usd <= 0:
            return None
        return (self.proceeds_usd + self.value_usd) / self.cost_usd

    def flag(self, text: str) -> None:
        if text and text not in self.flags:
            self.flags.append(text)

    def apply(self, ev: Event) -> None:
        if ev.kind == "buy":
            if self.buys == 0:
                self.first_buy_ts, self.first_buy_sig = ev.ts, ev.signature
            self.buys += 1
            self.bought += ev.amount
            self.balance += ev.amount
            self.cost_usd += ev.usd
        elif ev.kind == "sell":
            self.sells += 1
            self.sold += ev.amount
            self.balance -= ev.amount
            self.proceeds_usd += ev.usd
        elif ev.kind == "transfer_in":
            self.transfer_in += ev.amount
            self.balance += ev.amount
        elif ev.kind == "transfer_out":
            self.transfer_out += ev.amount
            self.balance -= ev.amount
        self.flag(ev.note)
        self.last_trade_ts = max(self.last_trade_ts, ev.ts)

    def to_dict(self) -> dict:
        multiple = self.multiple
        return {
            "mint": self.mint, "symbol": self.symbol,
            "cost_usd": round(self.cost_usd, 2), "proceeds_usd": round(self.proceeds_usd, 2),
            "value_usd": round(self.value_usd, 2), "profit_usd": round(self.realized_usd, 2),
            "multiple": round(multiple, 2) if multiple is not None else None,
            "buys": self.buys, "sells": self.sells,
            "first_buy_ts": self.first_buy_ts or None, "last_trade_ts": self.last_trade_ts or None,
            "launched_ts": self.launched_ts, "first_buy_sig": self.first_buy_sig or None,
            "verified": self.verified,
            "flags": list(self.flags),
        }


def build_positions(deltas, sol_usd, dust_usd: float = DUST_USD) -> list:
    """Replay a wallet's history (oldest first) into one Position per coin."""
    positions: dict = {}
    for delta in sorted(deltas, key=lambda d: (d.ts, d.slot)):
        for ev in trade_events(delta, sol_usd, dust_usd):
            positions.setdefault(ev.mint, Position(ev.mint)).apply(ev)
    return list(positions.values())


def apply_quotes(positions, quotes: dict, min_liquidity_usd: float = 1000.0) -> None:
    """Fill symbol / launch time and value what is still held at today's price.

    A coin whose pool has under `min_liquidity_usd` is treated as dead (worth $0),
    and a holding is never valued above half the pool, since that is about the
    most a seller could actually get out.
    """
    for pos in positions:
        quote = quotes.get(pos.mint)
        if quote:
            pos.symbol = pos.symbol or quote.symbol
            pos.price_usd, pos.liquidity_usd, pos.launched_ts = quote.price, quote.liquidity, quote.launched_ts
        held = max(pos.balance, 0.0)
        pos.value_usd = 0.0
        if not held or not quote or not quote.price:
            continue
        if quote.liquidity is not None and quote.liquidity < min_liquidity_usd:
            pos.flag("no liquidity (dead / rugged)")
            continue
        value = held * quote.price
        if quote.liquidity:
            value = min(value, quote.liquidity / 2)
        pos.value_usd = value
