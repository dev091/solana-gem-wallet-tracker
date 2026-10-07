"""Judge a wallet against the gem-hunter rules and explain the verdict."""
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field

from . import util
from .config import Criteria

STRICT = "STRICT"          # passes every rule
GEM_HUNTER = "GEM_HUNTER"  # has enough gems, but breaks another rule (e.g. some trades under 20x)
REJECTED = "REJECTED"
ERROR = "ERROR"
TIER_ORDER = {STRICT: 0, GEM_HUNTER: 1, REJECTED: 2, ERROR: 3}

SNIPE_SECONDS = 60  # bought within a minute of launch: sniper / insider territory


@dataclass
class WalletReport:
    """Positions of one wallet as returned by a data provider."""

    wallet: str
    positions: list
    history_complete: bool = True
    too_active: bool = False
    tx_count: int = 0
    source: str = ""
    identity: dict | None = None
    notes: list = field(default_factory=list)


@dataclass
class Verdict:
    tier: str
    reasons: list   # rules the wallet broke (empty = STRICT)
    flags: list     # warnings worth a look (insider signs etc.)
    stats: dict
    gems: list
    trades: list


def gem_profit(pos, crit: Criteria) -> float:
    return pos.total_usd if crit.count_unrealized else pos.realized_usd


def in_entry_range(pos, crit: Criteria) -> bool:
    return crit.entry_min_usd <= pos.cost_usd <= crit.entry_max_usd


def is_gem(pos, crit: Criteria) -> bool:
    return in_entry_range(pos, crit) and gem_profit(pos, crit) >= crit.gem_profit_usd


def evaluate(report: WalletReport, crit: Criteria, now: float | None = None) -> Verdict:
    now = now if now is not None else time.time()
    trades = [p for p in report.positions if p.cost_usd > 0]  # coins actually bought
    gems = [p for p in trades if is_gem(p, crit)]
    young_cutoff = now - crit.grace_hours * 3600
    judged = [p for p in trades if not (p.first_buy_ts and p.first_buy_ts > young_cutoff)]
    still_open = [p for p in trades if p.first_buy_ts and p.first_buy_ts > young_cutoff]
    weak = [p for p in judged if (p.multiple or 0.0) < crit.min_multiple]
    off_range = [p for p in trades if not in_entry_range(p, crit)]
    lr, hr = util.usd(crit.entry_min_usd), util.usd(crit.entry_max_usd)

    reasons = []
    if report.too_active:
        reasons.append(f"too active ({report.tx_count:,}+ transactions): bot / scalper, not a gem hunter")
    elif not report.history_complete:
        reasons.append("trade history incomplete, every trade could not be checked")
    if len(trades) > crit.max_tokens:
        reasons.append(f"traded {len(trades)} coins (> {crit.max_tokens}): bot / scalper")
    if len(gems) < crit.min_gems:
        reasons.append(f"{len(gems)} gem(s) ({lr}-{hr} in, +{util.usd(crit.gem_profit_usd)} out); "
                       f"needs {crit.min_gems}")
    if weak:
        worst = min((p.multiple or 0.0) for p in weak)
        reasons.append(f"{len(weak)} trade(s) under {crit.min_multiple:g}x (worst {worst:.2f}x)")
    if crit.all_entries_in_range and off_range:
        reasons.append(f"{len(off_range)} trade(s) with entry outside {lr}-{hr}")

    flags = []
    if report.identity:
        kind = report.identity.get("type")
        if kind and kind not in ("kol", "sns"):
            flags.append(f"data provider labels this wallet: {kind}")
    snipes = [p for p in gems if p.launched_ts and p.first_buy_ts
              and 0 <= p.first_buy_ts - p.launched_ts <= SNIPE_SECONDS]
    if snipes:
        flags.append(f"{len(snipes)} gem(s) bought within {SNIPE_SECONDS}s of launch: sniper / insider?")
    unbought = sum(p.proceeds_usd for p in report.positions if p.cost_usd <= 0 and p.proceeds_usd > 1000)
    if unbought:
        flags.append(f"sold {util.usd(unbought)} of coins it never bought (received by transfer): "
                     f"possible insider / dev-linked wallet")
    sent = [p for p in weak if p.transfer_out > 0.5 * max(p.bought, 1e-12)]
    if sent:
        flags.append(f"{len(sent)} weak trade(s) were coins sent to another wallet, "
                     f"so not necessarily real losses")

    multiples = sorted(p.multiple for p in judged if p.multiple is not None)
    stats = {
        "trades": len(trades),
        "judged": len(judged),
        "open": len(still_open),
        "gems": len(gems),
        "wins_min_multiple": sum(1 for m in multiples if m >= crit.min_multiple),
        "losses": sum(1 for m in multiples if m < 1),
        "min_multiple": round(multiples[0], 2) if multiples else None,
        "median_multiple": round(statistics.median(multiples), 2) if multiples else None,
        "best_multiple": round(multiples[-1], 2) if multiples else None,
        "invested_usd": round(sum(p.cost_usd for p in trades), 2),
        "realized_usd": round(sum(p.realized_usd for p in trades), 2),
        "gem_profit_usd": round(sum(gem_profit(p, crit) for p in gems), 2),
        "hit_rate": round(len(gems) / len(trades), 3) if trades else None,
        "tx_count": report.tx_count,
    }

    if not reasons:
        tier = STRICT
    elif len(gems) >= crit.min_gems:
        tier = GEM_HUNTER
    else:
        tier = REJECTED
    return Verdict(tier, reasons, flags, stats, gems, trades)
