"""Pump.fun on-chain helpers: no API key needed.

Every Pump.fun coin trades on a "bonding curve" account until it graduates, and
that account's history starts at launch.  Reading the oldest transactions of the
bonding curve tells us exactly who bought each coin early and how much they paid,
straight from the chain.
"""
from __future__ import annotations

import hashlib

from . import util
from .solana import delta_from_rpc_tx
from .trades import trade_events

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# ed25519 curve constants, used to tell program-derived addresses apart from real keys.
_P = 2 ** 255 - 19
_D = -121665 * pow(121666, _P - 2, _P) % _P


def _on_curve(key: bytes) -> bool:
    """True if `key` decodes to an ed25519 point (same test Solana runs for PDAs)."""
    y = (int.from_bytes(key, "little") & ((1 << 255) - 1)) % _P
    u = (y * y - 1) % _P
    v = (_D * y * y + 1) % _P
    if u == 0:
        return True
    ratio = u * pow(v, _P - 2, _P) % _P
    return pow(ratio, (_P - 1) // 2, _P) == 1


def b58encode(raw: bytes) -> str:
    num = int.from_bytes(raw, "big")
    out = ""
    while num:
        num, rem = divmod(num, 58)
        out = util.B58_ALPHABET[rem] + out
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + out


def find_program_address(seeds: list, program_id: str) -> tuple:
    """Solana's findProgramAddress: (address, bump)."""
    program = util.b58decode(program_id)
    for bump in range(255, -1, -1):
        digest = hashlib.sha256(b"".join(seeds) + bytes([bump]) + program + b"ProgramDerivedAddress").digest()
        if not _on_curve(digest):
            return b58encode(digest), bump
    raise ValueError("no valid program address")


def bonding_curve(mint: str) -> str:
    return find_program_address([b"bonding-curve", util.b58decode(mint)], PUMP_PROGRAM)[0]


def oldest_signatures(rpc, address: str, count: int, max_pages: int = 150) -> tuple:
    """The `count` oldest successful signatures of `address`. Returns (signatures, reached_start)."""
    newest_first, before = [], None
    for _ in range(max_pages):
        cfg = {"limit": 1000}
        if before:
            cfg["before"] = before
        page = rpc.call("getSignaturesForAddress", [address, cfg]) or []
        newest_first.extend(page)
        if len(page) < 1000:
            ok = [s["signature"] for s in reversed(newest_first) if s.get("err") is None]
            return ok[:count], True
        before = page[-1]["signature"]
        newest_first = newest_first[-2000:]  # only the tail can end up being the oldest
    return [], False


def early_buyers(rpc, mint: str, sol_usd, crit, early_txs: int = 250, workers: int = 6,
                 max_pages: int = 150) -> tuple:
    """Wallets that bought `mint` in its first `early_txs` trades with a $min-$max entry.

    Returns ([(wallet, usd_paid, ts)], note).
    """
    curve = bonding_curve(mint)
    signatures, reached = oldest_signatures(rpc, curve, early_txs, max_pages)
    if not reached:
        return [], f"more than {max_pages}k bonding-curve trades, launch not reached"
    if not signatures:
        return [], "no bonding-curve history (not a Pump.fun coin?)"
    buyers = {}
    for tx in rpc.transactions(signatures, workers=workers):
        if not tx:
            continue
        keys = (tx.get("transaction") or {}).get("message", {}).get("accountKeys") or []
        signers = [k.get("pubkey") for k in keys if isinstance(k, dict) and k.get("signer")]
        # Smart wallets (e.g. many Fomo app wallets) hold the coin without signing.
        holders = [b.get("owner") for b in (tx.get("meta") or {}).get("postTokenBalances") or []
                   if b.get("mint") == mint and b.get("owner")]
        for wallet in dict.fromkeys(signers + holders):
            if wallet == curve:  # the curve itself "buys" back whatever sellers dump
                continue
            delta = delta_from_rpc_tx(tx, wallet)
            if not delta:
                continue
            for ev in trade_events(delta, sol_usd):
                if ev.kind == "buy" and ev.mint == mint:
                    paid, first_ts = buyers.get(wallet, (0.0, ev.ts))
                    buyers[wallet] = (paid + ev.usd, min(first_ts, ev.ts))
    in_range = [(w, usd, ts) for w, (usd, ts) in buyers.items()
                if crit.entry_min_usd <= usd <= crit.entry_max_usd]
    return in_range, f"{len(buyers)} early buyer(s), {len(in_range)} in range"
