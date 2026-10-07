"""Prices: historical SOL/USD (to value each buy/sell) and current token prices."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import net, util
from .config import CACHE_DIR

HOUR = 3600
BLOCK = 300 * HOUR  # Coinbase returns at most 300 candles per request


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SolPrice:
    """Hourly SOL/USD prices, fetched lazily in 300-hour blocks and cached on disk."""

    def __init__(self, cache_file: Path = CACHE_DIR / "sol_usd_hourly.json"):
        self.cache_file = cache_file
        cached = util.load_json(cache_file, {})
        self.hourly = {int(k): float(v) for k, v in (cached.get("hourly") or {}).items()}
        self.done_blocks = set(cached.get("blocks") or [])
        self._tried = set()
        self._spot = None
        self._lock = threading.Lock()

    def at(self, ts: int) -> float:
        """SOL price in USD at unix time `ts` (hour resolution)."""
        if not ts:
            return self.spot()
        hour = ts - ts % HOUR
        with self._lock:
            if hour not in self.hourly:
                block = hour // BLOCK
                if block not in self.done_blocks and block not in self._tried:
                    self._load_block(block)
            price = self._nearest(hour)
        return price if price else self.spot()

    def _nearest(self, hour: int, max_gap_hours: int = 12):
        for k in range(max_gap_hours + 1):
            for h in (hour - k * HOUR, hour + k * HOUR):
                if h in self.hourly:
                    return self.hourly[h]
        return None

    def _load_block(self, block: int) -> None:
        self._tried.add(block)
        now_hour = util.now() // HOUR * HOUR
        start = block * BLOCK
        end = min(start + BLOCK - HOUR, now_hour)
        for fetch in (self._coinbase, self._binance, self._coingecko):
            try:
                got = fetch(start, end)
            except Exception:
                continue
            if got:
                self.hourly.update(got)
                break
        if start + BLOCK < now_hour - 2 * HOUR:  # only finished blocks are final
            self.done_blocks.add(block)
        self._save()

    @staticmethod
    def _coinbase(start: int, end: int) -> dict:
        rows = net.get_json("https://api.exchange.coinbase.com/products/SOL-USD/candles",
                            params={"granularity": HOUR, "start": _iso(start), "end": _iso(end)})
        # rows: [time, low, high, open, close, volume]
        return {int(r[0]): (float(r[3]) + float(r[4])) / 2 for r in rows or []}

    @staticmethod
    def _binance(start: int, end: int) -> dict:
        rows = net.get_json("https://data-api.binance.vision/api/v3/klines",
                            params={"symbol": "SOLUSDT", "interval": "1h", "startTime": start * 1000,
                                    "endTime": end * 1000, "limit": 1000})
        # rows: [open_time_ms, open, high, low, close, ...]
        return {int(r[0]) // 1000: (float(r[1]) + float(r[4])) / 2 for r in rows or []}

    @staticmethod
    def _coingecko(start: int, end: int) -> dict:
        data = net.get_json("https://api.coingecko.com/api/v3/coins/solana/market_chart/range",
                            params={"vs_currency": "usd", "from": start, "to": end + HOUR})
        out = {}
        for ms, price in (data or {}).get("prices") or []:
            ts = int(ms) // 1000
            out[ts - ts % HOUR] = float(price)
        return out

    def spot(self) -> float:
        if self._spot is None:
            for url, params in (("https://api.exchange.coinbase.com/products/SOL-USD/ticker", None),
                                ("https://data-api.binance.vision/api/v3/ticker/price", {"symbol": "SOLUSDT"})):
                try:
                    self._spot = float(net.get_json(url, params=params)["price"])
                    break
                except Exception:
                    continue
            else:
                if not self.hourly:
                    raise RuntimeError("could not get a SOL/USD price from Coinbase or Binance")
                self._spot = self.hourly[max(self.hourly)]
        return self._spot

    def _save(self) -> None:
        try:
            util.save_json(self.cache_file, {"hourly": {str(k): v for k, v in sorted(self.hourly.items())},
                                             "blocks": sorted(self.done_blocks)})
        except OSError:
            pass


@dataclass
class TokenQuote:
    mint: str
    symbol: str = ""
    price: float | None = None
    liquidity: float | None = None   # USD in the best pool (None = unknown)
    market_cap: float | None = None
    launched_ts: int | None = None   # earliest pool creation = launch time


def token_quotes(mints, log=None) -> dict:
    """Current price, liquidity, market cap and launch time per mint.

    DexScreener first (has liquidity + launch time), Jupiter for whatever is missing.
    """
    mints = list(dict.fromkeys(m for m in mints if m))
    quotes: dict = {}
    for chunk in util.chunks(mints, 30):
        try:
            pairs = net.get_json("https://api.dexscreener.com/tokens/v1/solana/" + ",".join(chunk))
        except Exception as exc:
            if log:
                log(f"   DexScreener lookup failed: {exc}")
            continue
        wanted = set(chunk)
        for pair in pairs or []:
            base = pair.get("baseToken") or {}
            mint = base.get("address")
            if mint not in wanted:
                continue
            quote = quotes.setdefault(mint, TokenQuote(mint))
            created = util.to_seconds(pair.get("pairCreatedAt"))
            if created and (quote.launched_ts is None or created < quote.launched_ts):
                quote.launched_ts = created
            liquidity = util.num((pair.get("liquidity") or {}).get("usd"))
            if quote.liquidity is None or liquidity > quote.liquidity:
                quote.liquidity = liquidity
                quote.price = util.num(pair.get("priceUsd")) or None
                quote.symbol = base.get("symbol") or quote.symbol
                quote.market_cap = util.num(pair.get("marketCap") or pair.get("fdv")) or None

    missing = [m for m in mints if m not in quotes or not quotes[m].price]
    for chunk in util.chunks(missing, 50):
        try:
            data = net.get_json("https://lite-api.jup.ag/price/v3", params={"ids": ",".join(chunk)})
        except Exception:
            continue
        if isinstance(data, dict) and isinstance(data.get("data"), dict):  # older v2 shape
            data = data["data"]
        for mint, info in (data or {}).items():
            if isinstance(info, dict) and (info.get("usdPrice") or info.get("price")):
                quote = quotes.setdefault(mint, TokenQuote(mint))
                quote.price = util.num(info.get("usdPrice") or info.get("price"))
    return quotes
