"""Decode meme-coin trades straight from Solana program logs.

Pump.fun, PumpSwap and Raydium LaunchLab (Bonk) are Anchor programs that log every
trade as a "Program data: <base64>" line. The first 8 bytes name the event
(sha256("event:<Name>")[:8]) and the rest is Borsh, laid out as in the public IDLs:
  pump      github.com/pump-fun/pump-public-docs  idl/pump.json
  pump_amm  github.com/pump-fun/pump-public-docs  idl/pump_amm.json
  launchlab github.com/raydium-io/raydium-idl     raydium_launchpad/raydium_launchpad.json

A log line belongs to whichever program is on top of the invoke stack, so a
transaction that routes through an aggregator is still attributed correctly.
Trailing event fields are optional: older events simply stop early.
"""
from __future__ import annotations

import base64
import hashlib
import struct
from dataclasses import dataclass, field

PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
LAUNCHLAB = "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
PROGRAMS = {PUMP: "pump", PUMP_AMM: "pumpswap", LAUNCHLAB: "launchlab"}

WSOL = "So11111111111111111111111111111111111111112"
DEFAULT_KEY = "11111111111111111111111111111111"
PUMP_DECIMALS = 6           # every pump.fun / LaunchLab coin
PUMP_SUPPLY = 1_000_000_000  # whole tokens

# Account layouts used to map a pool address to its coin (8-byte Anchor prefix included).
PUMP_AMM_POOL_BASE_MINT = 8 + 1 + 2 + 32                  # bump, index, creator
LAUNCHLAB_POOL_BASE_MINT = 8 + 8 + 5 + 10 * 8 + 5 * 8 + 32 + 32  # ..., vesting, configs

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    pad = len(raw) - len(raw.lstrip(b"\0"))
    return "1" * pad + out


def disc(name: str) -> bytes:
    return hashlib.sha256(f"event:{name}".encode()).digest()[:8]


class _Short(Exception):
    pass


class Reader:
    def __init__(self, raw: bytes, pos: int = 0):
        self.raw, self.pos = raw, pos

    def _take(self, n: int) -> bytes:
        if self.pos + n > len(self.raw):
            raise _Short
        chunk = self.raw[self.pos:self.pos + n]
        self.pos += n
        return chunk

    def u8(self):
        return self._take(1)[0]

    def u16(self):
        return struct.unpack("<H", self._take(2))[0]

    def u64(self):
        return struct.unpack("<Q", self._take(8))[0]

    def i64(self):
        return struct.unpack("<q", self._take(8))[0]

    def bool(self):
        return self._take(1)[0] != 0

    def key(self):
        return b58encode(self._take(32))

    def shareholders(self):
        """vec<Shareholder{address, share_bps u16}>: skipped, only the count is kept."""
        n = struct.unpack("<I", self._take(4))[0]
        self._take(34 * n)
        return n

    def string(self):
        return self._take(struct.unpack("<I", self._take(4))[0]).decode("utf-8", "replace")


def _read(raw: bytes, spec: list[tuple[str, str]], required: int) -> dict | None:
    """Read fields in order; fields past index `required` are optional (old layouts)."""
    r, out = Reader(raw, 8), {}
    for i, (name, kind) in enumerate(spec):
        try:
            out[name] = getattr(r, kind)()
        except _Short:
            return out if i >= required else None
    return out


PUMP_TRADE = [("mint", "key"), ("sol_amount", "u64"), ("token_amount", "u64"), ("is_buy", "bool"),
              ("user", "key"), ("timestamp", "i64"), ("virtual_sol_reserves", "u64"),
              ("virtual_token_reserves", "u64"), ("real_sol_reserves", "u64"),
              ("real_token_reserves", "u64"), ("fee_recipient", "key"), ("fee_basis_points", "u64"),
              ("fee", "u64"), ("creator", "key"), ("creator_fee_basis_points", "u64"),
              ("creator_fee", "u64"), ("track_volume", "bool"), ("total_unclaimed_tokens", "u64"),
              ("total_claimed_tokens", "u64"), ("current_sol_volume", "u64"),
              ("last_update_timestamp", "i64"), ("ix_name", "string"), ("mayhem_mode", "bool"),
              ("cashback_fee_basis_points", "u64"), ("cashback", "u64"),
              ("buyback_fee_basis_points", "u64"), ("buyback_fee", "u64"),
              ("shareholders", "shareholders"), ("quote_mint", "key"), ("quote_amount", "u64"),
              ("virtual_quote_reserves", "u64"), ("real_quote_reserves", "u64")]
PUMP_CREATE = [("name", "string"), ("symbol", "string"), ("uri", "string"), ("mint", "key"),
               ("bonding_curve", "key"), ("user", "key"), ("creator", "key"), ("timestamp", "i64"),
               ("virtual_token_reserves", "u64"), ("virtual_sol_reserves", "u64"),
               ("real_token_reserves", "u64"), ("token_total_supply", "u64"),
               ("token_program", "key"), ("is_mayhem_mode", "bool"), ("is_cashback_enabled", "bool"),
               ("quote_mint", "key")]
PUMP_COMPLETE = [("user", "key"), ("mint", "key"), ("bonding_curve", "key"), ("timestamp", "i64")]
AMM_BUY = [("timestamp", "i64"), ("base_amount_out", "u64"), ("max_quote_amount_in", "u64"),
           ("user_base_token_reserves", "u64"), ("user_quote_token_reserves", "u64"),
           ("pool_base_token_reserves", "u64"), ("pool_quote_token_reserves", "u64"),
           ("quote_amount_in", "u64"), ("lp_fee_basis_points", "u64"), ("lp_fee", "u64"),
           ("protocol_fee_basis_points", "u64"), ("protocol_fee", "u64"),
           ("quote_amount_in_with_lp_fee", "u64"), ("user_quote_amount_in", "u64"),
           ("pool", "key"), ("user", "key")]
AMM_SELL = [("timestamp", "i64"), ("base_amount_in", "u64"), ("min_quote_amount_out", "u64"),
            ("user_base_token_reserves", "u64"), ("user_quote_token_reserves", "u64"),
            ("pool_base_token_reserves", "u64"), ("pool_quote_token_reserves", "u64"),
            ("quote_amount_out", "u64"), ("lp_fee_basis_points", "u64"), ("lp_fee", "u64"),
            ("protocol_fee_basis_points", "u64"), ("protocol_fee", "u64"),
            ("quote_amount_out_without_lp_fee", "u64"), ("user_quote_amount_out", "u64"),
            ("pool", "key"), ("user", "key")]
AMM_CREATE_POOL = [("timestamp", "i64"), ("index", "u16"), ("creator", "key"), ("base_mint", "key"),
                   ("quote_mint", "key"), ("base_mint_decimals", "u8"),
                   ("quote_mint_decimals", "u8"), ("base_amount_in", "u64"),
                   ("quote_amount_in", "u64"), ("pool_base_amount", "u64"),
                   ("pool_quote_amount", "u64"), ("minimum_liquidity", "u64"),
                   ("initial_liquidity", "u64"), ("lp_token_amount_out", "u64"),
                   ("pool_bump", "u8"), ("pool", "key")]
LL_TRADE = [("pool_state", "key"), ("total_base_sell", "u64"), ("virtual_base", "u64"),
            ("virtual_quote", "u64"), ("real_base_before", "u64"), ("real_quote_before", "u64"),
            ("real_base_after", "u64"), ("real_quote_after", "u64"), ("amount_in", "u64"),
            ("amount_out", "u64"), ("protocol_fee", "u64"), ("platform_fee", "u64"),
            ("creator_fee", "u64"), ("share_fee", "u64"), ("trade_direction", "u8"),
            ("pool_status", "u8")]
LL_CREATE = [("pool_state", "key"), ("creator", "key"), ("config", "key"),
             ("decimals", "u8"), ("name", "string"), ("symbol", "string"), ("uri", "string")]

DECODERS = {
    (PUMP, disc("TradeEvent")): ("trade", PUMP_TRADE, 10),
    (PUMP, disc("CreateEvent")): ("create", PUMP_CREATE, 12),
    (PUMP, disc("CompleteEvent")): ("complete", PUMP_COMPLETE, 4),
    (PUMP_AMM, disc("BuyEvent")): ("amm_buy", AMM_BUY, 16),
    (PUMP_AMM, disc("SellEvent")): ("amm_sell", AMM_SELL, 16),
    (PUMP_AMM, disc("CreatePoolEvent")): ("amm_create", AMM_CREATE_POOL, 16),
    (LAUNCHLAB, disc("TradeEvent")): ("ll_trade", LL_TRADE, 16),
    (LAUNCHLAB, disc("PoolCreateEvent")): ("ll_create", LL_CREATE, 7),
}


@dataclass
class ChainEvent:
    """One normalized on-chain event.

    kind: trade | create | migrate | pool
    For trades, `quote` is the SOL (or stable) amount in lamports-style base units,
    `tokens` the coin amount in base units and `price` SOL per whole token after the trade.
    Pool events (PumpSwap, LaunchLab) may lack `mint` until the pool is resolved.
    """
    kind: str
    venue: str
    signature: str
    index: int
    slot: int = 0
    ts: int = 0
    mint: str = ""
    pool: str = ""
    user: str = ""
    side: str = ""          # buy | sell
    quote: int = 0
    tokens: int = 0
    price: float = 0.0      # quote per whole token (SOL unless quote_mint says otherwise)
    quote_mint: str = WSOL
    reserve_quote: int = 0  # reserves used for exact constant-product fills
    reserve_base: int = 0
    fee_bps: int = 0
    progress: float = 0.0   # bonding curve fill, 0..1 (pump / launchlab)
    extra: dict = field(default_factory=dict)

    def mcap_quote(self, supply: int = PUMP_SUPPLY) -> float:
        return self.price * supply


def _price(quote_reserve: int, base_reserve: int, quote_decimals: int = 9,
           base_decimals: int = PUMP_DECIMALS) -> float:
    if base_reserve <= 0:
        return 0.0
    return (quote_reserve / 10 ** quote_decimals) / (base_reserve / 10 ** base_decimals)


PUMP_INITIAL_REAL_TOKENS = 793_100_000 * 10 ** PUMP_DECIMALS


def _normalize(name: str, d: dict, venue: str, sig: str, idx: int, slot: int) -> ChainEvent | None:
    base = dict(venue=venue, signature=sig, index=idx, slot=slot)
    if name == "trade":
        qm = d.get("quote_mint") or WSOL
        qm = WSOL if qm == DEFAULT_KEY else qm
        vq, vb, amount = d["virtual_sol_reserves"], d["virtual_token_reserves"], d["sol_amount"]
        if qm != WSOL:  # coin quoted in a stablecoin: the SOL fields are not the curve
            vq, amount = d.get("virtual_quote_reserves") or vq, d.get("quote_amount") or amount
        qdec = 9 if qm == WSOL else 6
        fee_bps = d.get("fee_basis_points", 95) + d.get("creator_fee_basis_points", 30)
        progress = 1 - d["real_token_reserves"] / PUMP_INITIAL_REAL_TOKENS
        return ChainEvent("trade", mint=d["mint"], user=d["user"], ts=d["timestamp"],
                          side="buy" if d["is_buy"] else "sell", quote=amount,
                          tokens=d["token_amount"], price=_price(vq, vb, qdec), quote_mint=qm,
                          reserve_quote=vq, reserve_base=vb, fee_bps=fee_bps,
                          progress=max(0.0, min(1.0, progress)),
                          extra={"creator": d.get("creator", ""),
                                 "mayhem": bool(d.get("mayhem_mode"))}, **base)
    if name == "create":
        qm = d.get("quote_mint") or WSOL
        qm = WSOL if qm == DEFAULT_KEY else qm
        return ChainEvent("create", mint=d["mint"], user=d["user"], ts=d["timestamp"],
                          price=_price(d["virtual_sol_reserves"], d["virtual_token_reserves"]),
                          quote_mint=qm, reserve_quote=d["virtual_sol_reserves"],
                          reserve_base=d["virtual_token_reserves"],
                          extra={"name": d["name"][:64], "symbol": d["symbol"][:32],
                                 "creator": d["creator"], "bonding_curve": d["bonding_curve"],
                                 "supply": d["token_total_supply"] // 10 ** PUMP_DECIMALS,
                                 "mayhem": bool(d.get("is_mayhem_mode"))},
                          **base)
    if name == "complete":
        return ChainEvent("migrate", mint=d["mint"], user=d["user"], ts=d["timestamp"],
                          progress=1.0, **base)
    if name in ("amm_buy", "amm_sell"):
        buy = name == "amm_buy"
        b, q = d["pool_base_token_reserves"], d["pool_quote_token_reserves"]
        # Reserves are logged before the swap; move them past it.
        if buy:
            tokens, quote = d["base_amount_out"], d["quote_amount_in"]
            b, q = b - tokens, q + quote
        else:
            tokens, quote = d["base_amount_in"], d["quote_amount_out"]
            b, q = b + tokens, q - quote
        fee_bps = d["lp_fee_basis_points"] + d["protocol_fee_basis_points"]
        return ChainEvent("trade", pool=d["pool"], user=d["user"], ts=d["timestamp"],
                          side="buy" if buy else "sell", quote=quote, tokens=tokens,
                          price=_price(q, b), reserve_quote=q, reserve_base=b,
                          fee_bps=fee_bps + 30, progress=1.0, **base)
    if name == "amm_create":
        return ChainEvent("pool", mint=d["base_mint"], pool=d["pool"], user=d["creator"],
                          ts=d["timestamp"], quote_mint=d["quote_mint"],
                          reserve_quote=d["pool_quote_amount"], reserve_base=d["pool_base_amount"],
                          price=_price(d["pool_quote_amount"], d["pool_base_amount"],
                                       d["quote_mint_decimals"], d["base_mint_decimals"]),
                          extra={"base_decimals": d["base_mint_decimals"]}, **base)
    if name == "ll_trade":
        buy = d["trade_direction"] == 0
        vq = d["virtual_quote"] + d["real_quote_after"]
        vb = d["virtual_base"] - d["real_base_after"]
        tokens = abs(d["real_base_after"] - d["real_base_before"])
        quote = abs(d["real_quote_after"] - d["real_quote_before"])
        total = d["total_base_sell"] or 1
        return ChainEvent("trade", pool=d["pool_state"], side="buy" if buy else "sell",
                          quote=quote, tokens=tokens, price=_price(vq, vb), reserve_quote=vq,
                          reserve_base=vb, fee_bps=100, progress=min(1.0, d["real_base_after"] / total),
                          extra={"status": d["pool_status"]}, **base)
    if name == "ll_create":
        return ChainEvent("create", pool=d["pool_state"], user=d["creator"],
                          extra={"name": d["name"][:64], "symbol": d["symbol"][:32]}, **base)
    return None


def parse_logs(signature: str, logs: list[str], slot: int = 0) -> list[ChainEvent]:
    """All decodable events in one transaction's logs, attributed via the invoke stack."""
    stack: list[str] = []
    out: list[ChainEvent] = []
    for idx, line in enumerate(logs or ()):
        if line.startswith("Program data: "):
            if not stack:
                continue
            program = stack[-1]
            try:
                raw = base64.b64decode(line[14:])
            except ValueError:
                continue
            spec = DECODERS.get((program, raw[:8]))
            if not spec:
                continue
            name, layout, required = spec
            fields = _read(raw, layout, required)
            if fields is None:
                continue
            try:
                ev = _normalize(name, fields, PROGRAMS[program], signature, idx, slot)
            except (KeyError, ZeroDivisionError):
                continue
            if ev:
                out.append(ev)
        elif line.startswith("Program ") and " invoke [" in line:
            stack.append(line.split()[1])
        elif line.startswith("Program ") and (line.endswith(" success") or " failed" in line):
            parts = line.split()
            if stack and len(parts) > 1 and parts[1] == stack[-1]:
                stack.pop()
    return out


def pool_base_mint(program_venue: str, account_data: bytes) -> str:
    """The coin mint stored in a PumpSwap pool or LaunchLab pool_state account."""
    off = PUMP_AMM_POOL_BASE_MINT if program_venue == "pumpswap" else LAUNCHLAB_POOL_BASE_MINT
    if len(account_data) < off + 32:
        return ""
    return b58encode(account_data[off:off + 32])
