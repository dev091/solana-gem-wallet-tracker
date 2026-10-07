"""Jupiter's verified token list: the "verified coins only" rule and the whole-Solana gem universe.

Jupiter verifies tokens across every launchpad and DEX on Solana (Pump.fun, letsbonk, bags,
Meteora, MetaDAO, regular launches...). Its list also gives each token's first pool and launch
time, which is where the early-buyer search starts reading the chain.
"""
from __future__ import annotations

from datetime import datetime

from . import net, util
from .config import CACHE_DIR

URL = "https://lite-api.jup.ag/tokens/v2/tag"
CACHE_FILE = CACHE_DIR / "jup_verified.json"
MAX_AGE_SECONDS = 6 * 3600
NOT_GEMS = ("lst", "stock", "stable", "rwa")  # tags / names that are not trading coins


def _ts(iso) -> int | None:
    try:
        return int(datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp())
    except (TypeError, ValueError):
        return None


def load(log=print) -> dict:
    """{mint: {symbol, mcap, liquidity, launchpad, first_pool, launched_ts, organic, tags}}."""
    cached = util.load_json(CACHE_FILE, {})
    if cached.get("tokens") and util.now() - cached.get("fetched_at", 0) < MAX_AGE_SECONDS:
        return cached["tokens"]
    try:
        rows = net.get_json(URL, params={"query": "verified"}, timeout=90) or []
    except Exception as exc:
        if cached.get("tokens"):
            log(f"   Jupiter verified list unavailable ({exc}); using the cached copy")
            return cached["tokens"]
        raise
    tokens = {}
    for t in rows:
        if not isinstance(t, dict) or not util.is_address(t.get("id")):
            continue
        pool = t.get("firstPool") or {}
        tokens[t["id"]] = {"symbol": t.get("symbol") or "", "mcap": t.get("mcap"), "liquidity": t.get("liquidity"),
                           "launchpad": t.get("launchpad"), "first_pool": pool.get("id"),
                           "launched_ts": _ts(pool.get("createdAt")), "organic": t.get("organicScore"),
                           "tags": t.get("tags") or []}
    util.save_json(CACHE_FILE, {"fetched_at": util.now(), "tokens": tokens})
    return tokens


def recent_gems(tokens: dict, min_mcap: float = 2e6, max_age_days: float | None = 365, min_organic: float = 40,
                limit: int = 40) -> list:
    """Verified coins of every kind (DeFi, AI, infra, memes; any DEX or launchpad) launched in the
    last `max_age_days` (None = any age) that are now worth `min_mcap`+: from a launch price,
    that is a 50x-1000x run. [(mint, symbol, info)], biggest first."""
    cutoff = util.now() - max_age_days * 86400 if max_age_days else 0
    out = []
    for mint, t in tokens.items():
        text = " ".join([t.get("symbol") or ""] + [str(x) for x in t.get("tags") or []]).lower()
        if any(word in text for word in NOT_GEMS) or "usd" in (t.get("symbol") or "").lower():
            continue
        if (t.get("mcap") or 0) < min_mcap or not t.get("launched_ts") or t["launched_ts"] < cutoff:
            continue
        if t.get("organic") is not None and t["organic"] < min_organic:
            continue
        out.append((mint, t.get("symbol") or "", t))
    out.sort(key=lambda row: -(row[2].get("mcap") or 0))
    return out[:limit]


def mark(positions, tokens: dict | None) -> None:
    """Set pos.verified to True/False (left None when the list could not be loaded)."""
    if not tokens:
        return
    for pos in positions:
        pos.verified = pos.mint in tokens
