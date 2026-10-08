"""Rug filter every algo runs before a buy, and the tail-aware position size.

One function and one set of limits for every algo, so no algo can quietly trade the coins the
others refuse. Fail closed: a fact we cannot see (partial holder history, a missing safety field
for a coin on another DEX) is a reason to skip the coin, never a pass.

Pump, PumpSwap and LaunchLab coins have mint and freeze authority revoked and their LP burned by
the protocol, so only the market checks apply to them. Coins on any other DEX ("jup" venue) must
also prove the token and pool facts through `Meta`, filled from free sources (RPC account data,
DexScreener, a read-only Jupiter quote).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .chain_events import WSOL

PROTOCOL_SAFE = frozenset({"pump", "pumpswap", "launchlab"})


@dataclass(frozen=True)
class Limits:
    """Pre-registered 2026-10-07 (BRIEF.md, Risk and rug avoidance). Never loosened per algo."""
    min_age_s: float = 30.0            # no sniping
    min_liq_mult: float = 20.0         # pool quote reserve >= this x our buy
    min_liq_usd: float = 50_000.0      # other DEXes
    max_top10: float = 0.30            # top-10 trader wallets' share of supply (curve and pool excluded)
    max_dev: float = 0.05              # creator's net holding
    max_snipers: float = 0.20          # still held by wallets that bought within SNIPE_S of the create
    dev_sell_cooldown_s: float = 120.0
    min_lp_locked: float = 0.90        # share of LP burned or locked (other DEXes)
    max_sell_impact: float = 0.05      # round-trip price impact of a Jupiter quote at our size


LIMITS = Limits()


@dataclass(frozen=True)
class Meta:
    """Facts from outside the trade tape. None means unknown, which fails the check that needs it."""
    top10_share: float | None = None
    dev_share: float | None = None           # pump-family coins seen without their create need these
    sniper_share: float | None = None        # two, the others may leave them unknown
    dev_last_sell_ms: int | None = None
    mint_authority: bool | None = None       # True: someone can still mint
    freeze_authority: bool | None = None     # True: someone can still freeze holders
    bad_extensions: tuple | None = None      # Token-2022: transfer fee, hook, permanent delegate, pausable
    lp_locked: float | None = None
    liquidity_usd: float | None = None
    sell_impact: float | None = None         # None: no sell route (honeypot)


class Verdict(NamedTuple):
    ok: bool
    reasons: tuple


def check(st, now_ms: int, size_sol: float, meta: Meta | None = None, limits: Limits = LIMITS) -> Verdict:
    """May an algo buy `size_sol` of this coin now? Collects every failed check, in a fixed order."""
    m, lim, out = meta or Meta(), limits, []
    if st.age_s(now_ms) < lim.min_age_s:
        out.append("young")

    safe = st.venue in PROTOCOL_SAFE
    sol_pool = st.quote_mint == WSOL and st.reserve_quote > 0
    deep = (not sol_pool or st.reserve_quote / 1e9 >= lim.min_liq_mult * size_sol) and \
        (safe and sol_pool or (m.liquidity_usd or 0) >= lim.min_liq_usd)
    if not deep:
        out.append("thin")

    if st.seen_create:                       # every trade since the create: our own holder book
        own_dev = st.holders.get(st.creator, 0.0) / st.supply if st.creator and st.supply else 0.0
        top10 = max(st.top_holder_share(10), m.top10_share or 0.0)
        dev = max(own_dev, m.dev_share or 0.0)
        snipers = max(st.sniper_share(), m.sniper_share or 0.0)
    else:
        top10, dev, snipers = m.top10_share, m.dev_share, m.sniper_share
        if safe and (dev is None or snipers is None):
            top10 = None                     # a pump coin's dev and launch wallets are known risks
    if top10 is None:
        out.append("partial_history")
    elif top10 > lim.max_top10:
        out.append("concentrated")
    if (dev or 0.0) > lim.max_dev:
        out.append("dev_heavy")
    if (snipers or 0.0) > lim.max_snipers:
        out.append("bundled")
    cut = now_ms - lim.dev_sell_cooldown_s * 1000
    if (m.dev_last_sell_ms or 0) >= cut or _dev_sold_since(st, cut):
        out.append("dev_dumping")

    if not safe:
        if m.mint_authority is not False:
            out.append("mint_authority")
        if m.freeze_authority is not False:
            out.append("freeze_authority")
        if m.bad_extensions is None or m.bad_extensions:
            out.append("token2022")
        if m.lp_locked is None or m.lp_locked < lim.min_lp_locked:
            out.append("lp_unlocked")
        if m.sell_impact is None or m.sell_impact > lim.max_sell_impact:
            out.append("unsellable")
    return Verdict(not out, tuple(out))


def _dev_sold_since(st, cut_ms: float) -> bool:
    if not st.creator:                       # unknown creator: never match anonymous trades
        return False
    for t in reversed(st.trades):            # kept in rx order: stop at the first older trade
        if t.rx < cut_ms:
            return False
        if t.side == "sell" and t.user == st.creator:
            return True
    return False


def risk_size_frac(worst_loss: float, kelly: float | None = None, max_risk: float = 0.05,
                   cap: float = 0.25) -> float:
    """Equity fraction to put in one position. `worst_loss` is the p99 loss per trade measured on FIT
    at live latency, rugs that gap through the stop included: one such loss costs at most `max_risk`
    of equity. Kelly (already haircut) wins when it is smaller; no edge, no bet."""
    if not 0 < worst_loss <= 1:
        raise ValueError(f"worst_loss must be in (0, 1], got {worst_loss}")
    frac = min(cap, max_risk / worst_loss)
    return frac if kelly is None else max(0.0, min(frac, kelly))
