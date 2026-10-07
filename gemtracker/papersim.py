"""Paper execution: per-algo books with a realistic fill model. Paper only, no orders.

Fill model (an intent is fixed before any later data is consulted):
  decision  at the local time the triggering data arrived (now_ms)
  arrival   decision + latency_ms; the order meets the coin's state as it was at that
            moment (after the last trade received at or before arrival)
  price     exact constant-product output on that state's reserves, minus the venue fee
  slippage  a buy fails if the price rose more than its max_slippage by arrival; the
            network + priority fee is still paid, as on chain
  costs     venue fee and network fee are kept in separate columns
Marks are liquidation values (what a full sell would return now), never the last price.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .chain_events import WSOL
from .strategy import Buy, Sell

LAMPORTS = 1e9
TOKEN_UNIT = 1e6


@dataclass
class SimConfig:
    latency_ms: int = 2500         # receive-clock: public feed lag p90 ~2.1 s + send ~0.5 s
    # The public PumpSwap stream arrives later (lag p90 ~5 s on 2026-10-07).
    venue_latency_ms: dict = field(default_factory=lambda: {"pumpswap": 5500})
    tx_fee_sol: float = 0.001      # base fee + priority fee + tip, per transaction
    start_usd: float = 100.0
    min_order_sol: float = 0.005
    max_open_positions: int = 10


@dataclass
class Fill:
    algo: str
    side: str
    mint: str
    decision_ms: int
    arrival_ms: int
    status: str                 # filled | rejected
    reason: str = ""
    why: str = ""              # rejection cause
    sol: float = 0.0           # SOL paid (buy) / received (sell), before tx fee
    venue_fee_sol: float = 0.0
    tx_fee_sol: float = 0.0
    tokens: float = 0.0
    price: float = 0.0         # SOL per token at the fill
    decision_price: float = 0.0
    mcap_sol: float = 0.0
    sol_usd: float = 0.0
    venue: str = ""
    pnl_sol: float = 0.0       # realized on sells


@dataclass
class Position:
    mint: str
    tokens: float = 0.0
    cost_sol: float = 0.0      # incl. venue + tx fees
    cost_usd: float = 0.0
    opened_ms: int = 0
    buys: int = 0
    sells: int = 0
    realized_sol: float = 0.0


@dataclass
class Pending:
    intent: object
    decision_ms: int
    arrival_ms: int
    decision_price: float


def buy_out(sol_in: float, fee_bps: int, rq: int, rb: int) -> tuple[float, float]:
    """(tokens out, venue fee in SOL) for spending sol_in on reserves rq/rb (base units)."""
    fee = sol_in * fee_bps / 10_000
    net = (sol_in - fee) * LAMPORTS
    if rq <= 0 or rb <= 0 or net <= 0:
        return 0.0, fee
    return (rb * net / (rq + net)) / TOKEN_UNIT, fee


def sell_out(tokens: float, fee_bps: int, rq: int, rb: int) -> tuple[float, float]:
    """(SOL out after fee, venue fee in SOL) for selling `tokens` whole tokens."""
    t = tokens * TOKEN_UNIT
    if rq <= 0 or rb <= 0 or t <= 0:
        return 0.0, 0.0
    gross = rq * t / (rb + t) / LAMPORTS
    fee = gross * fee_bps / 10_000
    return gross - fee, fee


class Book:
    def __init__(self, algo: str, cfg: SimConfig, sol_usd: float, ledger: Path | None = None):
        self.algo = algo
        self.cfg = cfg
        self.start_sol = cfg.start_usd / sol_usd
        self.cash_sol = self.start_sol
        self.positions: dict[str, Position] = {}
        self.pending: list[Pending] = []
        self.closed: list[dict] = []
        self.fills = 0
        self.rejects = 0
        self.fees_venue = 0.0
        self.fees_tx = 0.0
        self.realized_usd = 0.0
        self.ledger = ledger
        if ledger:
            ledger.parent.mkdir(parents=True, exist_ok=True)

    def has(self, mint: str) -> bool:
        return mint in self.positions or any(p.intent.mint == mint for p in self.pending)

    def pending_buy_sol(self) -> float:
        return sum(p.intent.sol for p in self.pending if isinstance(p.intent, Buy))

    def free_sol(self) -> float:
        return self.cash_sol - self.pending_buy_sol()

    def equity_sol(self, market) -> float:
        total = self.cash_sol
        for mint, pos in self.positions.items():
            st = market.get(mint)
            if st:
                total += sell_out(pos.tokens, st.fee_bps, st.reserve_quote, st.reserve_base)[0]
        return total

    def _log(self, fill: Fill) -> None:
        if self.ledger:
            with open(self.ledger, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(fill), separators=(",", ":")) + "\n")


class PaperSim:
    """Runs strategies against the market and keeps one Book per strategy."""

    def __init__(self, strategies, cfg: SimConfig, sol_usd, out_dir: Path | None = None):
        self.cfg = cfg
        self.sol_usd = sol_usd  # callable -> current SOL/USD
        self.strategies = list(strategies)
        price = sol_usd()
        self.books = {s.name: Book(s.name, cfg, price,
                                   (out_dir / f"{s.name}.jsonl") if out_dir else None)
                      for s in self.strategies}

    # ----- intents -----
    def submit(self, strat, intents, now_ms: int, market) -> None:
        book = self.books[strat.name]
        for it in intents or ():
            st = market.get(it.mint)
            if st is None or not st.reserve_quote:
                continue
            if isinstance(it, Buy):
                if st.quote_mint != WSOL:
                    continue  # quoted in another token: our SOL book cannot price it
                if it.mint in book.positions or book.has(it.mint):
                    continue  # one entry at a time per coin; adds come after the fill
                if len(book.positions) >= self.cfg.max_open_positions:
                    continue
                it.sol = min(it.sol, book.free_sol() - self.cfg.tx_fee_sol)
                if it.sol < self.cfg.min_order_sol:
                    continue
            elif isinstance(it, Sell):
                if it.mint not in book.positions or any(
                        isinstance(p.intent, Sell) and p.intent.mint == it.mint for p in book.pending):
                    continue
            latency = self.cfg.venue_latency_ms.get(st.venue, self.cfg.latency_ms)
            book.pending.append(Pending(it, now_ms, now_ms + latency, st.price))

    # ----- fills -----
    def settle(self, mint: str | None, now_ms: int, market) -> None:
        """Fill every pending order whose arrival time has come.

        Call with the coin's mint *before* applying an event received at now_ms, so the
        order sees the state as of its arrival; call with mint=None on the clock tick.
        """
        for strat in self.strategies:
            book = self.books[strat.name]
            if not book.pending:
                continue
            due = [p for p in book.pending
                   if p.arrival_ms <= now_ms and (mint is None or p.intent.mint == mint)]
            for p in due:
                book.pending.remove(p)
                fill = self._fill(book, p, market)
                strat.on_fill(fill, book)

    def _fill(self, book: Book, p: Pending, market) -> Fill:
        it, st = p.intent, market.get(p.intent.mint)
        side = "buy" if isinstance(it, Buy) else "sell"
        f = Fill(book.algo, side, it.mint, p.decision_ms, p.arrival_ms, "rejected", it.reason,
                 decision_price=p.decision_price, sol_usd=self.sol_usd())
        tx = self.cfg.tx_fee_sol
        if st is None or not st.reserve_quote:
            f.why = "no market state"
            return self._reject(book, f, tx)
        f.venue, f.price, f.mcap_sol = st.venue, st.price, st.mcap
        if side == "buy":
            if p.decision_price and st.price > p.decision_price * (1 + it.max_slippage):
                f.why = f"slippage {st.price / p.decision_price - 1:.0%}"
                return self._reject(book, f, tx)
            spend = min(it.sol, book.cash_sol - tx)
            if spend < self.cfg.min_order_sol:
                f.why = "cash"
                return self._reject(book, f, 0.0)
            tokens, fee = buy_out(spend, st.fee_bps, st.reserve_quote, st.reserve_base)
            if tokens <= 0:
                f.why = "no liquidity"
                return self._reject(book, f, tx)
            book.cash_sol -= spend + tx
            pos = book.positions.get(it.mint) or Position(it.mint, opened_ms=p.arrival_ms)
            pos.tokens += tokens
            pos.cost_sol += spend + tx
            pos.cost_usd += (spend + tx) * f.sol_usd
            pos.buys += 1
            book.positions[it.mint] = pos
            f.sol, f.tokens = spend, tokens
        else:
            pos = book.positions[it.mint]
            frac = 1.0 if it.fraction >= 0.999 else max(0.0, it.fraction)
            tokens = pos.tokens * frac
            out, fee = sell_out(tokens, st.fee_bps, st.reserve_quote, st.reserve_base)
            share = tokens / pos.tokens if pos.tokens else 1.0
            cost_sol, cost_usd = pos.cost_sol * share, pos.cost_usd * share
            book.cash_sol += out - tx
            pos.tokens -= tokens
            pos.cost_sol -= cost_sol
            pos.cost_usd -= cost_usd
            pos.sells += 1
            pnl = out - tx - cost_sol
            pos.realized_sol += pnl
            book.realized_usd += (out - tx) * f.sol_usd - cost_usd
            f.sol, f.tokens, f.pnl_sol = out, tokens, pnl
            if frac == 1.0 or pos.tokens * st.price < 1e-6:
                book.closed.append({"mint": it.mint, "opened_ms": pos.opened_ms,
                                    "closed_ms": p.arrival_ms, "pnl_sol": pos.realized_sol,
                                    "buys": pos.buys, "sells": pos.sells})
                del book.positions[it.mint]
        f.status, f.venue_fee_sol, f.tx_fee_sol = "filled", fee, tx
        book.fills += 1
        book.fees_venue += fee
        book.fees_tx += tx
        book._log(f)
        return f

    def _reject(self, book: Book, f: Fill, tx: float) -> Fill:
        book.cash_sol -= tx
        book.fees_tx += tx
        f.tx_fee_sol = tx
        book.rejects += 1
        book._log(f)
        return f

    # ----- reporting -----
    def summary(self, market) -> list[dict]:
        rows = []
        usd = self.sol_usd()
        for name, b in self.books.items():
            eq = b.equity_sol(market)
            wins = sum(1 for c in b.closed if c["pnl_sol"] > 0)
            rows.append({"algo": name, "equity_usd": round(eq * usd, 2),
                         "return": round(eq / b.start_sol - 1, 4),
                         "realized_usd": round(b.realized_usd, 2),
                         "cash_sol": round(b.cash_sol, 4), "open": len(b.positions),
                         "pending": len(b.pending), "closed": len(b.closed),
                         "win_rate": round(wins / len(b.closed), 3) if b.closed else None,
                         "fills": b.fills, "rejects": b.rejects,
                         "venue_fees_sol": round(b.fees_venue, 4), "tx_fees_sol": round(b.fees_tx, 4)})
        return sorted(rows, key=lambda r: -r["equity_usd"])

    def dispatch(self, hook: str, market, now_ms: int, *args) -> None:
        for strat in self.strategies:
            book = self.books[strat.name]
            try:
                intents = getattr(strat, hook)(*args, now_ms, book) if hook != "on_tick" \
                    else strat.on_tick(market, now_ms, book)
            except Exception as exc:  # one broken algo must not stop the others
                intents = []
                book.errors = getattr(book, "errors", 0) + 1
                if getattr(book, "errors", 0) <= 3:
                    print(f"[{strat.name}] {hook} error: {exc!r}", flush=True)
            if intents:
                self.submit(strat, intents, now_ms, market)
