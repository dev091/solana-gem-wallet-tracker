"""The shared baselines every reconstruction is compared against (paper only).

  base_random      random entry on new coins (seeded, reproducible) + fixed TP / stop / time exit
  base_hold60      buy every new coin at a fixed age, sell 60 s later
  base_elite_copy  buy when any elite buys, sell when that elite sells or after a time stop:
                   the explicit copy-trading benchmark (latency makes it an honest one)

Report every algo as a difference from base_random (same universe, same exit rule) and
from base_hold60. All parameters are class attributes so a report can state them.
"""
from __future__ import annotations

from ..strategy import Buy, Sell
from .swing_base_lib import Tracked, unit_hash


class BaseRandom(Tracked):
    name = "base_random"
    compound, max_price_impact = False, None   # baselines stay simple and fixed
    description = "random entry on new coins, fixed TP/stop/time exit (seeded)"
    seed = 20261007
    enter_prob = 0.10          # share of eligible coins entered
    max_age_s = 30.0           # a coin is 'new' until this age
    min_buyers_10s = 1         # at least one buyer seen, so there is a market
    size_frac = 0.05
    take_profit, tp_fraction = 0.50, 1.0
    stop_loss = 0.30
    max_hold_s = 120.0

    def __init__(self):
        super().__init__()
        self.decided: set[str] = self.per_mint(set())

    def eligible(self, st, now_ms: int) -> bool:
        return (st.seen_create and st.venue in self.venues and not st.migrated
                and st.age_s(now_ms) <= self.max_age_s
                and st.window(now_ms, 10)["unique_buyers"] >= self.min_buyers_10s)

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        out = self.exits_on_trade(st, now_ms, book)
        if st.mint in self.decided or book.has(st.mint):
            return out
        if not self.eligible(st, now_ms):
            if st.age_s(now_ms) > self.max_age_s:
                self.decided.add(st.mint)   # too old now, never reconsider
            return out
        self.decided.add(st.mint)           # one draw per coin, at its first eligible trade
        if unit_hash(self.seed, st.mint) < self.enter_prob:
            out.append(Buy(st.mint, self.size_sol(book), "random"))
        return out


class BaseHold60(Tracked):
    name = "base_hold60"
    compound, max_price_impact = False, None
    description = "buy every new coin at a fixed age, sell after 60 s"
    entry_age_s = 5.0          # first trade received at or after this age
    max_age_s = 30.0
    size_frac = 0.05
    max_hold_s = 60.0

    def __init__(self):
        super().__init__()
        self.decided: set[str] = self.per_mint(set())

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        out = self.exits_on_trade(st, now_ms, book)
        if st.mint in self.decided or book.has(st.mint) or not st.seen_create or st.migrated:
            return out
        age = st.age_s(now_ms)
        if age < self.entry_age_s:
            return out
        self.decided.add(st.mint)
        if age <= self.max_age_s:
            out.append(Buy(st.mint, self.size_sol(book), f"hold60 at {age:.0f}s"))
        return out


class BaseEliteCopy(Tracked):
    name = "base_elite_copy"
    compound, max_price_impact = False, None
    description = "copy-trade: buy when any elite buys, sell when that elite sells or on time stop"
    follow: tuple = ()         # elite names to copy; empty = all
    size_frac = 0.05
    max_hold_s = 300.0
    stop_loss = 0.50           # a wide safety stop; the elite's own sell is the real exit
    max_followed_sol = None    # ignore elite buys bigger than this (None = any)

    def __init__(self):
        super().__init__()
        self.leader: dict[str, str] = {}   # mint -> elite we are copying

    def _elite_event(self, st, ev, now_ms: int, side: str, book):
        """The elite record for this very event: same ms AND the event's wallet is that elite
        (another wallet trading in the same ms must not look like a copy signal)."""
        lst = st.elite_buys if side == "buy" else st.elite_sells
        if not lst or lst[-1][0] != now_ms:
            return None
        hit = lst[-1]
        m = getattr(book, "market", None) or self._market()
        names = getattr(m, "elite_names", None)
        if names is None or not ev.user or names.get(ev.user) != hit[1]:
            return None
        return hit

    def on_trade(self, st, ev, now_ms: int, book) -> list:
        out = self.exits_on_trade(st, now_ms, book)
        if ev.side == "buy":
            hit = self._elite_event(st, ev, now_ms, "buy", book)
            if hit and (not self.follow or hit[1] in self.follow) and not book.has(st.mint) \
                    and (self.max_followed_sol is None or hit[2] <= self.max_followed_sol):
                out.append(Buy(st.mint, self.size_sol(book), f"copy {hit[1]}"))  # leader set on the fill
        else:
            hit = self._elite_event(st, ev, now_ms, "sell", book)
            if hit and st.mint in book.positions and self.leader.get(st.mint) == hit[1] \
                    and not any(isinstance(s, Sell) for s in out):
                out.append(Sell(st.mint, 1.0, f"{hit[1]} sold"))
        return out

    def on_fill(self, fill, book) -> None:
        super().on_fill(fill, book)
        if fill.side == "buy" and fill.status == "filled" and fill.reason.startswith("copy "):
            self.leader[fill.mint] = fill.reason[5:]   # remembered from the fill, not the intent
        if fill.mint not in book.positions and not any(p.intent.mint == fill.mint for p in book.pending):
            self.leader.pop(fill.mint, None)
