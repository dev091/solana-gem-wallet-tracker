"""The interface every paper-trading algorithm implements.

A strategy sees the market only through callbacks, at the local time the data
arrived, and answers with intents. It never sees fills before they happen: the
simulator decides later, at arrival time, whether and at what price an intent fills.

    class MyAlgo(Strategy):
        name = "my-algo"
        def on_trade(self, st, ev, now_ms, book):
            if st.age_s(now_ms) < 20 and st.window(now_ms, 10)["unique_buyers"] >= 8:
                return [Buy(st.mint, sol=book.cash_sol * 0.1, reason="early flow")]
            return []

Positions in `book` change only on simulated fills; a pending order shows in
`book.pending` until then. `book.equity()` is the liquidation value of cash plus positions.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Buy:
    mint: str
    sol: float                 # SOL to spend, venue fee included
    reason: str = ""
    max_slippage: float = 0.25  # fail (fee still paid) if the price rose more by arrival
    add: bool = False          # True: may add to a coin already held (never while a buy is pending)


@dataclass
class Sell:
    mint: str
    fraction: float = 1.0      # of the tokens currently held
    reason: str = ""


class Strategy:
    """Base class: override any callback; each returns a list of Buy/Sell intents."""

    name = "base"
    description = ""
    # Venues this algo trades: pump (curve), pumpswap, launchlab.
    venues = ("pump", "pumpswap", "launchlab")

    def on_create(self, st, now_ms: int, book) -> list:
        """A new coin was launched (st.seen_create is True)."""
        return []

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        """Any trade on a coin, after `st` was updated with it."""
        return []

    def on_tick(self, market, now_ms: int, book) -> list:
        """Called about once a second; use it for time-based exits."""
        return []

    def on_fill(self, fill, book) -> None:
        """A simulated fill (or rejection) for this strategy's own order."""
