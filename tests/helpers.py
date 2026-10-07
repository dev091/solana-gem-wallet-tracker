"""Test helpers: deterministic fake addresses and Solana RPC transaction builders."""
import hashlib

from gemtracker.util import B58_ALPHABET

SOL = 1_000_000_000


def b58encode(raw: bytes) -> str:
    num = int.from_bytes(raw, "big")
    out = ""
    while num:
        num, rem = divmod(num, 58)
        out = B58_ALPHABET[rem] + out
    pad = len(raw) - len(raw.lstrip(b"\0"))
    return "1" * pad + out


def addr(seed: str) -> str:
    """A valid-looking Solana address derived from `seed`."""
    return b58encode(hashlib.sha256(seed.encode()).digest())


def rpc_tx(wallet, signature, ts, *, sol_before=10 * SOL, sol_after=10 * SOL, pre_tokens=(), post_tokens=(),
           err=None, extra_keys=()):
    """getTransaction (jsonParsed) result. *_tokens: (mint, raw_amount, decimals[, owner])."""
    keys = [{"pubkey": wallet, "signer": True, "writable": True}] + [
        {"pubkey": k, "signer": False, "writable": True} for k in extra_keys]

    def balances(rows):
        out = []
        for i, row in enumerate(rows):
            mint, amount, decimals = row[:3]
            owner = row[3] if len(row) > 3 else wallet
            out.append({"accountIndex": i + 1, "mint": mint, "owner": owner,
                        "uiTokenAmount": {"amount": str(amount), "decimals": decimals}})
        return out

    return {
        "blockTime": ts, "slot": ts // 2,
        "meta": {"err": err, "fee": 5000,
                 "preBalances": [sol_before] + [0] * len(extra_keys),
                 "postBalances": [sol_after] + [0] * len(extra_keys),
                 "preTokenBalances": balances(pre_tokens), "postTokenBalances": balances(post_tokens)},
        "transaction": {"signatures": [signature], "message": {"accountKeys": keys}},
    }
