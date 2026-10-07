"""Scan candidate wallets, judge them, and write the results the dashboard and tracker use."""
from __future__ import annotations

import time

from . import config, util
from .criteria import ERROR, GEM_HUNTER, REJECTED, STRICT, TIER_ORDER, Verdict, evaluate

MAX_TRADES_SAVED = 60


def wallet_result(cand, report, verdict: Verdict) -> dict:
    trades = sorted(verdict.trades, key=lambda p: p.first_buy_ts or 0, reverse=True)
    return {
        "wallet": cand.wallet,
        "tier": verdict.tier,
        "labels": list(cand.labels),
        "sources": list(cand.sources),
        "gem_hits_in_search": cand.gem_hits,
        "stats": verdict.stats,
        "reasons": verdict.reasons,
        "flags": verdict.flags,
        "notes": list(report.notes),
        "data_source": report.source,
        "gems": [p.to_dict() for p in sorted(verdict.gems, key=lambda p: p.realized_usd, reverse=True)],
        "trades": [p.to_dict() for p in trades[:MAX_TRADES_SAVED]],
    }


def error_result(cand, message: str) -> dict:
    return {"wallet": cand.wallet, "tier": ERROR, "labels": list(cand.labels), "sources": list(cand.sources),
            "gem_hits_in_search": cand.gem_hits, "stats": {}, "reasons": [message], "flags": [],
            "notes": [], "gems": [], "trades": []}


def skipped_result(cand, reason: str) -> dict:
    out = error_result(cand, reason)
    out["tier"] = REJECTED
    return out


def scan(candidates: list, provider, crit, max_wallets: int, log=print, time_budget_min: float = 0) -> list:
    todo = candidates[:max_wallets]
    skip = {}
    if hasattr(provider, "prescreen") and todo:
        skip = provider.prescreen([c.wallet for c in todo])
    deadline = time.monotonic() + time_budget_min * 60 if time_budget_min else None
    results = []
    for i, cand in enumerate(todo, 1):
        if deadline and time.monotonic() > deadline:
            log(f"Time budget of {time_budget_min:g} min used up: {len(todo) - i + 1} wallet(s) left for next run")
            break
        tag = ", ".join(cand.labels[:2]) or ", ".join(cand.sources)
        log(f"[{i}/{len(todo)}] {cand.wallet}  ({tag})")
        if cand.wallet in skip:
            results.append(skipped_result(cand, skip[cand.wallet]))
            log(f"   → REJECTED: {skip[cand.wallet]}")
            continue
        try:
            report = provider.report(cand.wallet)
            verdict = evaluate(report, crit)
        except Exception as exc:
            results.append(error_result(cand, f"{type(exc).__name__}: {exc}"))
            log(f"   → ERROR: {exc}")
            continue
        results.append(wallet_result(cand, report, verdict))
        s = verdict.stats
        log(f"   → {verdict.tier}: {s['gems']} gem(s), {s['trades']} trade(s), "
            f"worst {util.mult(s['min_multiple'])}, realized {util.usd(s['realized_usd'])}"
            + (f"  | {verdict.reasons[0]}" if verdict.reasons else ""))
    results.sort(key=lambda r: (TIER_ORDER.get(r["tier"], 9), -(r["stats"].get("gems") or 0),
                                -(r["stats"].get("realized_usd") or 0)))
    return results


def save_results(results: list, crit, provider_name: str, source_status: dict) -> dict:
    counts = {tier.lower(): sum(1 for r in results if r["tier"] == tier)
              for tier in (STRICT, GEM_HUNTER, REJECTED, ERROR)}
    payload = {
        "generated_at": util.now(),
        "provider": provider_name,
        "criteria": crit.as_dict(),
        "sources": source_status,
        "counts": {"scanned": len(results), **counts},
        "wallets": results,
    }
    util.save_json(config.DOCS_DATA_DIR / "wallets.json", payload, js_var="GEM_WALLETS")
    tracked = [{"wallet": r["wallet"], "tier": r["tier"], "label": (r["labels"] or [""])[0],
                "gems": r["stats"].get("gems", 0)}
               for r in results if r["tier"] in (STRICT, GEM_HUNTER)]
    util.save_json(config.DATA_DIR / "tracked.json", {"generated_at": payload["generated_at"], "wallets": tracked})
    return payload
