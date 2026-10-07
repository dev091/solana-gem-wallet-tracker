"""Read a wallet's on-chain history and turn each transaction into balance changes.

Works with any Solana RPC (free public RPC, Helius, QuickNode, ...).  When a
Helius key is set, Helius' parsed-history API (100 transactions per request)
is tried first, with plain RPC as the fallback.
"""
from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from itertools import count
from urllib.parse import urlsplit

from . import net
from .config import SOL_MINT

LAMPORTS = 1_000_000_000
# JSON-RPC errors worth retrying: rate limits, node behind, block not yet available.
RETRY_RPC_CODES = {429, -32429, -32005, -32004, -32014, -32016}


class RpcError(Exception):
    pass


@dataclass
class TxDelta:
    """Net effect of one transaction on one wallet."""

    signature: str
    ts: int                                     # unix seconds, 0 if unknown
    slot: int
    sol: float                                  # SOL + wrapped-SOL change, fees included
    tokens: dict = field(default_factory=dict)  # mint -> signed token amount change


@dataclass
class History:
    deltas: list
    tx_count: int    # transactions seen, including failed ones
    complete: bool   # False when the wallet has more than max_txs transactions
    source: str      # "helius" or "rpc"


def _to_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(float(value))


def _make_delta(signature, ts, slot, lamports: int, raw: dict, decimals: dict) -> TxDelta:
    wsol = raw.pop(SOL_MINT, 0)  # wrapped SOL (9 decimals) is just SOL
    tokens = {mint: amount / 10 ** decimals.get(mint, 0) for mint, amount in raw.items() if amount}
    return TxDelta(signature or "", _to_int(ts), _to_int(slot), (lamports + wsol) / LAMPORTS, tokens)


def delta_from_rpc_tx(tx: dict | None, wallet: str) -> TxDelta | None:
    """Balance changes of `wallet` from a getTransaction result (json or jsonParsed)."""
    if not tx:
        return None
    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return None
    message = (tx.get("transaction") or {}).get("message") or {}
    raw_keys = message.get("accountKeys") or []
    keys = [k.get("pubkey") if isinstance(k, dict) else k for k in raw_keys]
    if raw_keys and not isinstance(raw_keys[0], dict):
        # "json" encoding lists lookup-table accounts separately; jsonParsed already merges them.
        loaded = meta.get("loadedAddresses") or {}
        keys += list(loaded.get("writable") or []) + list(loaded.get("readonly") or [])

    lamports = 0
    if wallet in keys:
        i = keys.index(wallet)
        pre, post = meta.get("preBalances") or [], meta.get("postBalances") or []
        if i < len(pre) and i < len(post):
            lamports = post[i] - pre[i]

    raw, decimals = {}, {}
    for sign, balances in ((-1, meta.get("preTokenBalances")), (1, meta.get("postTokenBalances"))):
        for bal in balances or []:
            if bal.get("owner") != wallet or not bal.get("mint"):
                continue
            amount = bal.get("uiTokenAmount") or {}
            mint = bal["mint"]
            raw[mint] = raw.get(mint, 0) + sign * _to_int(amount.get("amount"))
            decimals[mint] = _to_int(amount.get("decimals"))

    signatures = (tx.get("transaction") or {}).get("signatures") or [""]
    return _make_delta(signatures[0], tx.get("blockTime"), tx.get("slot"), lamports, raw, decimals)


def delta_from_helius_tx(tx: dict, wallet: str) -> TxDelta | None:
    """Balance changes of `wallet` from one Helius parsed-history transaction."""
    if not isinstance(tx, dict) or tx.get("transactionError"):
        return None
    lamports, raw, decimals = 0, {}, {}
    for account in tx.get("accountData") or []:
        if account.get("account") == wallet:
            lamports += _to_int(account.get("nativeBalanceChange"))
        for change in account.get("tokenBalanceChanges") or []:
            if change.get("userAccount") != wallet or not change.get("mint"):
                continue
            amount = change.get("rawTokenAmount") or {}
            mint = change["mint"]
            raw[mint] = raw.get(mint, 0) + _to_int(amount.get("tokenAmount"))
            decimals[mint] = _to_int(amount.get("decimals"))
    return _make_delta(tx.get("signature"), tx.get("timestamp"), tx.get("slot"), lamports, raw, decimals)


class SolanaRpc:
    """Minimal JSON-RPC client with pacing and retries."""

    def __init__(self, url: str, rps: float | None = None, timeout: float = 60.0):
        self.url = url
        self.timeout = timeout
        host = urlsplit(url).hostname or ""
        if rps is None:
            # The free public endpoint allows ~40 getTransaction calls / 10s per IP.
            rps = 3.5 if host == "api.mainnet-beta.solana.com" else 9.0
        net.set_rate(host, rps)
        self._ids = count(1)
        self._lock = threading.Lock()

    def call(self, method: str, params: list, retries: int = 6):
        for attempt in range(retries + 1):
            with self._lock:
                request_id = next(self._ids)
            reply = net.post_json(self.url, {"jsonrpc": "2.0", "id": request_id,
                                             "method": method, "params": params}, timeout=self.timeout)
            if not isinstance(reply, dict):
                raise RpcError(f"{method}: unexpected reply {str(reply)[:100]}")
            error = reply.get("error")
            if not error:
                return reply.get("result")
            code = error.get("code")
            if code in RETRY_RPC_CODES and attempt < retries:
                time.sleep(min(1.5 * 2 ** attempt, 30.0))
                continue
            raise RpcError(f"{method} failed: {error.get('message')} (code {code})")
        raise AssertionError("unreachable")

    def signatures(self, address: str, max_count: int = 1000, until: str | None = None):
        """Signature infos, newest first. Returns (infos, complete)."""
        infos, before = [], None
        page_size = max(1, min(1000, max_count))
        while len(infos) < max_count:
            cfg = {"limit": page_size}
            if before:
                cfg["before"] = before
            if until:
                cfg["until"] = until
            page = self.call("getSignaturesForAddress", [address, cfg]) or []
            infos.extend(page)
            if len(page) < page_size:
                return infos, True
            before = page[-1]["signature"]
        return infos[:max_count], False

    def transaction(self, signature: str):
        return self.call("getTransaction", [signature, {"encoding": "jsonParsed",
                                                        "maxSupportedTransactionVersion": 0,
                                                        "commitment": "confirmed"}])

    def transactions(self, signatures: list, workers: int = 6, on_progress=None) -> list:
        """getTransaction for many signatures in parallel, results in input order."""
        out = [None] * len(signatures)
        failures = []
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {pool.submit(self.transaction, sig): i for i, sig in enumerate(signatures)}
            for done, future in enumerate(as_completed(futures), 1):
                try:
                    out[futures[future]] = future.result()
                except Exception as exc:  # one bad transaction should not sink a whole wallet
                    failures.append(exc)
                if on_progress and done % 250 == 0:
                    on_progress(done, len(signatures))
        if len(failures) > max(3, len(signatures) // 20):
            raise RpcError(f"{len(failures)}/{len(signatures)} getTransaction calls failed, "
                           f"e.g. {failures[0]}")
        return out


class HeliusHistory:
    """Helius parsed transaction history: 100 transactions per request."""

    URL = "https://api.helius.xyz/v0/addresses/{}/transactions"
    _CONTINUE = re.compile(r"parameter set to ([1-9A-HJ-NP-Za-km-z]{64,100})")

    def __init__(self, api_key: str):
        self.key = api_key
        net.set_rate("api.helius.xyz", 8)

    def history(self, wallet: str, max_txs: int) -> History:
        deltas, seen, before = [], 0, None
        while seen < max_txs:
            params = {"api-key": self.key, "limit": 100}
            if before:
                params["before"] = before
            page = net.get_json(self.URL.format(wallet), params=params)
            if isinstance(page, dict):
                # Helius sometimes asks to continue from a signature instead of returning a page.
                found = self._CONTINUE.search(str(page.get("error", "")))
                if found and found.group(1) != before:
                    before = found.group(1)
                    continue
                raise RpcError(f"Helius: {page.get('error') or str(page)[:120]}")
            if not page:
                return History(deltas, seen, True, "helius")
            if seen == 0 and "accountData" not in page[0]:
                raise RpcError("Helius reply has no accountData field")
            for tx in page:
                delta = delta_from_helius_tx(tx, wallet)
                if delta:
                    deltas.append(delta)
            seen += len(page)
            before = page[-1].get("signature")
            if not before:
                break
        return History(deltas, seen, False, "helius")


def fetch_history(wallet: str, rpc: SolanaRpc, helius: HeliusHistory | None = None,
                  max_txs: int = 3000, workers: int = 6, log=print) -> History:
    """All of a wallet's balance changes, or an incomplete History if it has > max_txs."""
    if helius is not None:
        try:
            return helius.history(wallet, max_txs)
        except Exception as exc:
            log(f"   Helius history failed ({exc}); falling back to plain RPC")

    infos, complete = rpc.signatures(wallet, max_txs)
    if not complete:
        # Gem hunters make few, careful trades. Thousands of transactions = bot/scalper.
        return History([], len(infos), False, "rpc")
    signatures = [info["signature"] for info in infos if info.get("err") is None]
    if len(signatures) > 500:
        log(f"   fetching {len(signatures)} transactions over RPC (takes a while on the free RPC)…")
    progress = (lambda d, t: log(f"   … {d}/{t}")) if len(signatures) > 500 else None
    txs = rpc.transactions(signatures, workers=workers, on_progress=progress)
    deltas = [d for d in (delta_from_rpc_tx(tx, wallet) for tx in txs) if d]
    return History(deltas, len(infos), True, "rpc")
