"""Where candidate wallets come from.

Leaderboards (top N each):
  pump-board - Pump.fun's official PnL leaderboard, rolling 24h / 7d / 30d (no key)
  kolscan    - Kolscan, the KOL leaderboard Pump.fun bought and uses (no key, page scrape)
  fomo       - Fomo app leaderboard 24h / 7d / 30d via the unofficial fomoapi.io (FOMOAPI_KEY)
  st-kols    - Solana Tracker KOL leaderboard, all-time / 7d / 30d (SOLANATRACKER_API_KEY)
  st-top     - Solana Tracker top traders by ROI with 4+ closed coins (SOLANATRACKER_API_KEY)
  gmgn       - GMGN smart-money + KOL wallets (GMGN_API_KEY)
Gem search (the most direct way to find repeat gem hunters):
  pump-gems  - take Pump.fun's biggest coins (+ wallets/gem_tokens.txt), list each coin's
               traders who put in $100-$500 and took out $100k+, rank wallets by how many
               coins they did that on (needs SOLANATRACKER_API_KEY or GMGN_API_KEY)
  pump-early - no key: read each of those coins' bonding curve on-chain and list who bought
               in the first trades with a $100-$500 entry; wallets that did it on 2+ coins
  verified-early - no key, whole Solana: Jupiter-verified coins from any launchpad or DEX that
               went from launch to $2M+ in the last 120 days; reads each one's first pool on-chain
               and keeps wallets that bought 2+ of them in their first trades
Fomo without a key:
  fomo-top50 - snapshot of the Fomo app's top-50 profit leaderboard with Solana wallets
               (wallets/fomo_top50.json); both the main and the in-app Fomo wallet are checked
Manual:
  seeds      - wallets/seeds.txt (paste addresses from the Fomo app, Pump.fun, X, anywhere)
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import asdict, dataclass, field

from . import config, net, util
from .config import Criteria

ALL_SOURCES = ["seeds", "verified-early", "pump-board", "kolscan", "fomo-top50", "fomo", "st-kols", "st-top",
               "gmgn", "pump-gems"]
# Labels on traders that are infrastructure, not people picking coins.
NOT_A_TRADER = {"bot", "pool", "exchange", "sandwich_bot", "dex_bot", "bundler"}


class SourceError(Exception):
    pass


@dataclass
class Candidate:
    wallet: str
    labels: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    gem_hits: int = 0    # coins (from gem search) where this wallet did $100-500 -> $100k+
    early_hits: int = 0  # big Pump.fun coins this wallet bought early with a $100-500 entry


class CandidateBook:
    def __init__(self):
        self.by_wallet: dict = {}

    def add(self, wallet: str, source: str, label: str = "") -> Candidate | None:
        if not util.is_address(wallet):
            return None
        cand = self.by_wallet.setdefault(wallet, Candidate(wallet))
        if source not in cand.sources:
            cand.sources.append(source)
        if label and label not in cand.labels:
            cand.labels.append(label)
        return cand

    def ordered(self) -> list:
        """Gem-search hits first, then hand-picked seeds, then wallets on several boards."""
        order = list(self.by_wallet.values())
        index = {c.wallet: i for i, c in enumerate(order)}
        return sorted(order, key=lambda c: (-c.gem_hits, -c.early_hits, "seeds" not in c.sources,
                                            -len(c.sources), index[c.wallet]))

    def to_list(self) -> list:
        return [asdict(c) for c in self.ordered()]

    @classmethod
    def from_list(cls, rows: list) -> "CandidateBook":
        book = cls()
        for row in rows or []:
            if util.is_address(row.get("wallet")):
                book.by_wallet[row["wallet"]] = Candidate(row["wallet"], list(row.get("labels") or []),
                                                          list(row.get("sources") or []),
                                                          int(row.get("gem_hits") or 0),
                                                          int(row.get("early_hits") or 0))
        return book


# ---------------------------------------------------------------- leaderboards

def seeds() -> list:
    return [(w, label or "seed") for w, label in util.read_wallet_list(config.SEEDS_FILE)]


def fomo_top50(top: int = 50) -> list:
    """Fomo app top-50 profit leaderboard snapshot: main wallet + in-app Fomo wallet per trader."""
    data = util.load_json(config.FOMO_TOP50_FILE, {})
    rows = sorted(data.get("wallets") or [], key=lambda r: r.get("rank") or 999)
    if not rows:
        raise SourceError(f"{config.FOMO_TOP50_FILE.name} missing or empty")
    out = []
    for row in rows[:top]:
        who = (f"Fomo top-50 #{row.get('rank')} @{row.get('handle')} "
               f"({util.usd(row.get('pnl_usd'))} PnL, {row.get('trades')} trades)")
        if util.is_address(row.get("solana")):
            out.append((row["solana"], who))
        if util.is_address(row.get("fomo_solana")):
            out.append((row["fomo_solana"], who + " · in-app wallet"))
    return out


def kolscan(top: int) -> list:
    from .leaderboard import parse_kolscan
    page = net.get_text("https://kolscan.io/leaderboard", headers={"Accept": "text/html"})
    rows = parse_kolscan(page)
    if rows:
        return [(r.wallet, f"Kolscan daily #{r.rank} {r.name} ({util.usd(r.pnl_usd)})") for r in rows[:top]]
    wallets = []  # layout changed: fall back to bare account links
    for match in re.finditer(r"/account/(" + util.ADDRESS_PATTERN + ")", page):
        if util.is_address(match.group(1)) and match.group(1) not in wallets:
            wallets.append(match.group(1))
    if not wallets:
        raise SourceError("no wallets found on kolscan.io/leaderboard (page layout changed?)")
    return [(w, f"Kolscan/Pump.fun leaderboard #{i}") for i, w in enumerate(wallets[:top], 1)]


def pump_board(top: int) -> list:
    """Pump.fun's official PnL leaderboard (rolling 24h / 7d / 30d). Each window counts as its
    own source, so wallets on several windows rank higher as candidates."""
    from .leaderboard import PERIODS, pump_board as fetch
    out = []
    for period in PERIODS:
        for r in fetch(period, limit=max(top, 20))[:top]:
            out.append((r.wallet, f"Pump.fun {period} #{r.rank} {r.name} ({util.usd(r.pnl_usd)})",
                        f"pump.fun {period}"))
    return out


def _first_list(data):
    """The first list of objects inside a JSON reply, wherever the API put it."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("traders", "leaderboard", "data", "results", "items", "list", "users"):
            if key in data:
                found = _first_list(data[key])
                if found:
                    return found
        for value in data.values():
            found = _first_list(value)
            if found:
                return found
    return []


def fomo(top: int, key: str) -> list:
    if not key:
        raise SourceError("FOMOAPI_KEY not set (Fomo's leaderboard is only inside the app; "
                          "fomoapi.io is an unofficial API for it). Or paste Fomo wallets into wallets/seeds.txt")
    out = []
    for window in ("24h", "7d", "30d"):
        data = net.get_json(f"https://api.fomoapi.io/v2/leaderboard/{window}", params={"limit": top},
                            headers={"authorization": f"Bearer {key}"})
        for i, row in enumerate(_first_list(data)[:top], 1):
            if not isinstance(row, dict):
                continue
            wallets = row.get("wallets") or {}
            sol = wallets.get("solana") if isinstance(wallets, dict) else None
            sol = sol if isinstance(sol, list) else [sol or row.get("wallet") or row.get("address")]
            handle = row.get("handle") or row.get("username") or row.get("displayName") or ""
            rank = row.get("rank") or i
            for wallet in sol:
                if util.is_address(wallet):
                    out.append((wallet, f"Fomo {window} #{rank}" + (f" @{handle}" if handle else "")))
    if not out:
        raise SourceError("Fomo leaderboard reply had no Solana wallets")
    return out


def _st_get(key: str, path: str, params: dict):
    if not key:
        raise SourceError("SOLANATRACKER_API_KEY not set")
    net.set_rate("data.solanatracker.io", 4)
    return net.get_json("https://data.solanatracker.io" + path, params=params,
                        headers={"x-api-key": key}) or {}


def _identity_name(row: dict) -> str:
    ident = row.get("identity") or {}
    return ident.get("name") or ident.get("twitter") or ""


def solanatracker_kols(top: int, key: str) -> list:
    out = []
    boards = [("/v2/pnl/leaderboard/kols", {}, "all-time"),
              ("/v2/pnl/leaderboard/kols/period", {"period": "7d"}, "7d"),
              ("/v2/pnl/leaderboard/kols/period", {"period": "30d"}, "30d")]
    for path, extra, name in boards:
        data = _st_get(key, path, {"sort": "realized", "direction": "desc", "limit": top, **extra})
        for i, row in enumerate(data.get("traders") or [], 1):
            who = _identity_name(row)
            out.append((row.get("wallet"), f"KOL {name} #{i}" + (f" {who}" if who else "")))
    return out


def solanatracker_top(top: int, key: str) -> list:
    # Highest ROI with at least 4 closed coins: small entries that became huge exits rank first.
    data = _st_get(key, "/v2/pnl/leaderboard/top",
                   {"sort": "roi", "direction": "desc", "limit": max(top, 50),
                    "minClosedTokens": 4, "excludeArbitrage": "true"})
    out = []
    for i, row in enumerate(data.get("traders") or [], 1):
        ident = row.get("identity") or {}
        if ident.get("type") in NOT_A_TRADER:
            continue
        who = _identity_name(row)
        out.append((row.get("wallet"), f"top ROI #{i}" + (f" {who}" if who else "")))
    return out


def _gmgn_get(key: str, path: str, params: dict):
    if not key:
        raise SourceError("GMGN_API_KEY not set (create one at gmgn.ai/ai)")
    net.set_rate("openapi.gmgn.ai", 2)
    params = {**params, "timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
    data = net.get_json("https://openapi.gmgn.ai" + path, params=params,
                        headers={"X-APIKEY": key}) or {}
    if data.get("code") not in (0, None):
        raise SourceError(f"GMGN {path}: {data.get('message') or data.get('error') or data.get('code')}")
    return data.get("data")


def gmgn(top: int, key: str) -> list:
    out = []
    for kind, name in (("smartmoney", "GMGN smart money"), ("kol", "GMGN KOL")):
        data = _gmgn_get(key, f"/v1/user/{kind}", {"chain": "sol", "limit": 200})
        seen = []
        for row in _first_list(data):
            wallet = row.get("maker")
            if util.is_address(wallet) and wallet not in seen:
                seen.append(wallet)
                info = row.get("maker_info") or {}
                who = info.get("twitter_username") or info.get("name") or ""
                out.append((wallet, name + (f" @{who}" if who else "")))
            if len(seen) >= top * 2:
                break
    return out


# ---------------------------------------------------------------- gem search

def pumpfun_top_coins(limit: int) -> list:
    """Pump.fun's biggest coins by market cap: [(mint, symbol)]."""
    data = net.get_json("https://frontend-api-v3.pump.fun/coins",
                        params={"offset": 0, "limit": limit, "sort": "market_cap", "order": "DESC",
                                "includeNsfw": "false"},
                        headers={"Origin": "https://pump.fun", "Referer": "https://pump.fun/"})
    coins = []
    for row in _first_list(data):
        if isinstance(row, dict) and util.is_address(row.get("mint")):
            coins.append((row["mint"], row.get("symbol") or ""))
    if not coins:
        raise SourceError("pump.fun returned no coins")
    return coins[:limit]


def geckoterminal_pump_coins(limit: int) -> list:
    """Fallback coin list: busiest PumpSwap pools (graduated Pump.fun coins) on GeckoTerminal."""
    coins, seen = [], set()
    for page in range(1, 11):
        data = net.get_json("https://api.geckoterminal.com/api/v2/networks/solana/dexes/pumpswap/pools",
                            params={"page": page, "sort": "h24_volume_usd_desc"})
        pools = (data or {}).get("data") or []
        for pool in pools:
            base = ((pool.get("relationships") or {}).get("base_token") or {}).get("data") or {}
            mint = str(base.get("id") or "").split("_", 1)[-1]
            name = str((pool.get("attributes") or {}).get("name") or "").split(" / ")[0]
            if util.is_address(mint) and mint not in seen:
                seen.add(mint)
                coins.append((mint, name))
        if not pools or len(coins) >= limit:
            break
    if not coins:
        raise SourceError("GeckoTerminal returned no PumpSwap pools")
    return coins[:limit]


def _gem_traders_solanatracker(key: str, mint: str, crit: Criteria) -> list:
    data = _st_get(key, f"/v2/pnl/tokens/{mint}/traders",
                   {"sort": "realized", "direction": "desc", "limit": 100})
    out = []
    for row in data.get("traders") or []:
        invested = util.num(row.get("invested"))
        realized = ((row.get("pnl") or {}).get("token") or {}).get("realized")
        realized = util.num(realized, util.num(row.get("proceeds")) - invested)
        if realized < crit.gem_profit_usd:
            break  # sorted by realized profit, nothing below can qualify
        if (row.get("identity") or {}).get("type") in NOT_A_TRADER:
            continue
        if crit.entry_min_usd <= invested <= crit.entry_max_usd:
            out.append((row.get("wallet"), invested, realized))
    return out


def _as_set(value) -> set:
    if isinstance(value, (list, tuple, set)):
        return {str(v) for v in value}
    return {str(value)} if value else set()


def _gem_traders_gmgn(key: str, mint: str, crit: Criteria) -> list:
    data = _gmgn_get(key, "/v1/market/token_top_traders",
                     {"chain": "sol", "address": mint, "limit": 100, "order_by": "profit", "direction": "desc"})
    out = []
    for row in _first_list(data):
        invested = util.num(row.get("history_bought_cost"))
        realized = util.num(row.get("realized_profit"))
        tags = _as_set(row.get("tags")) | _as_set(row.get("maker_token_tags"))
        if tags & NOT_A_TRADER or row.get("addr_type") == 2 or row.get("transfer_in"):
            continue
        if crit.entry_min_usd <= invested <= crit.entry_max_usd and realized >= crit.gem_profit_usd:
            out.append((row.get("address"), invested, realized))
    return out


def gem_search(book: CandidateBook, coins: list, crit: Criteria, st_key: str, gmgn_key: str, log=print,
               deadline: float | None = None) -> int:
    """For each coin, add every wallet that turned $100-$500 into $100k+ on it. Returns wallets added."""
    if not st_key and not gmgn_key:
        raise SourceError("gem search needs SOLANATRACKER_API_KEY or GMGN_API_KEY "
                          "(to see who made money on each coin)")
    added = 0
    for i, (mint, symbol) in enumerate(coins, 1):
        if _out_of_time(deadline, "gem search", i - 1, len(coins), log):
            break
        name = symbol or util.short(mint)
        try:
            hits = (_gem_traders_solanatracker(st_key, mint, crit) if st_key
                    else _gem_traders_gmgn(gmgn_key, mint, crit))
        except Exception as exc:
            log(f"   [{i}/{len(coins)}] {name}: lookup failed ({exc})")
            continue
        for wallet, invested, realized in hits:
            cand = book.add(wallet, "gem-search", f"{name}: {util.usd(invested)} -> +{util.usd(realized)}")
            if cand:
                cand.gem_hits += 1
                added += 1
        log(f"   [{i}/{len(coins)}] {name}: {len(hits)} wallet(s) did "
            f"{util.usd(crit.entry_min_usd)}-{util.usd(crit.entry_max_usd)} -> +{util.usd(crit.gem_profit_usd)}")
    return added


def _out_of_time(deadline, what: str, done: int, total: int, log) -> bool:
    if deadline is not None and time.monotonic() > deadline:
        log(f"   time budget for {what} used up after {done}/{total} coin(s)")
        return True
    return False


def early_search(book: CandidateBook, coins: list, crit: Criteria, early_txs: int, min_hits: int,
                 log=print, deadline: float | None = None, source: str = "pump-early") -> int:
    """No-key gem search: early buyers of coins that became big, read from the chain.
    `coins` rows are (mint, symbol) or (mint, symbol, first_pool)."""
    from .pumpfun import early_buyers
    from .prices import SolPrice
    from .solana import SolanaRpc
    rpc, sol = SolanaRpc(config.rpc_url()), SolPrice()
    seen: dict = {}
    for i, coin in enumerate(coins, 1):
        if _out_of_time(deadline, "early search", i - 1, len(coins), log):
            break
        mint, symbol, pool = coin[0], coin[1], (coin[2] if len(coin) > 2 else None)
        name = symbol or util.short(mint)
        try:
            buyers, note = early_buyers(rpc, mint, sol.at, crit, early_txs=early_txs, pool=pool)
        except Exception as exc:
            log(f"   [{i}/{len(coins)}] {name}: failed ({exc})")
            continue
        log(f"   [{i}/{len(coins)}] {name}: {note}")
        for wallet, paid, _ts in buyers:
            seen.setdefault(wallet, []).append(f"{name} early {util.usd(paid)}")
    added = 0
    for wallet, hits in seen.items():
        if len(hits) >= min_hits:
            cand = book.add(wallet, source, f"early buyer on {len(hits)} big coins: " + ", ".join(hits[:3]))
            if cand:
                cand.early_hits = max(cand.early_hits, len(hits))
                added += 1
    return added


def gem_coins_list(gem_coins: int, log=print) -> list:
    coins = [(mint, label) for mint, label in util.read_wallet_list(config.GEM_TOKENS_FILE)]
    if gem_coins > 0:
        try:
            coins += pumpfun_top_coins(gem_coins)
        except Exception as exc:
            log(f"   pump.fun top coins unavailable ({exc}); trying GeckoTerminal")
            try:
                coins += geckoterminal_pump_coins(gem_coins)
            except Exception as exc2:
                log(f"   GeckoTerminal unavailable too ({exc2}); using wallets/gem_tokens.txt only")
    coins = list(dict(coins).items())  # de-duplicate, keep order
    if not coins:
        raise SourceError("no coins to search (pump.fun unreachable and wallets/gem_tokens.txt empty)")
    return coins


# ---------------------------------------------------------------- all together

def discover(sources: list, top: int, gem_coins: int, crit: Criteria, log=print,
             early_txs: int = 250, min_early_hits: int = 2, deadline: float | None = None):
    """Collect candidates from every requested source. Returns (book, status per source)."""
    st_key, gmgn_key, fomo_key = (config.env("SOLANATRACKER_API_KEY"), config.env("GMGN_API_KEY"),
                                  config.env("FOMOAPI_KEY"))
    book, status = CandidateBook(), {}
    boards = {
        "seeds": lambda: seeds(),
        "fomo-top50": lambda: fomo_top50(),
        "kolscan": lambda: kolscan(top),
        "pump-board": lambda: pump_board(top),
        "fomo": lambda: fomo(top, fomo_key),
        "st-kols": lambda: solanatracker_kols(top, st_key),
        "st-top": lambda: solanatracker_top(top, st_key),
        "gmgn": lambda: gmgn(top, gmgn_key),
    }
    for source in sources:
        if source in ("pump-gems", "pump-early", "verified-early"):
            continue
        if source not in boards:
            status[source] = {"ok": False, "error": "unknown source"}
            continue
        try:
            rows = boards[source]()
            # a row may name its own source (e.g. "pump.fun weekly"), else the source key is used
            added = len({row[0] for row in rows
                         if book.add(row[0], row[2] if len(row) > 2 else source, row[1])})
            status[source] = {"ok": True, "wallets": added}
            log(f"✔ {source}: {added} wallet(s)")
        except Exception as exc:
            status[source] = {"ok": False, "error": str(exc)}
            log(f"✘ {source}: {exc}")

    if "verified-early" in sources:
        try:
            from . import verified
            from .pumpfun import bonding_curve
            gems = verified.recent_gems(verified.load(log), limit=gem_coins)
            # Pump.fun coins start on their bonding curve, older than any pool Jupiter lists.
            vcoins = [(m, sym, bonding_curve(m) if t.get("launchpad") == "pump.fun" else t.get("first_pool"))
                      for m, sym, t in gems if t.get("first_pool") or t.get("launchpad") == "pump.fun"]
            log(f"… on-chain early-buyer search over {len(vcoins)} verified coin(s) from every launchpad")
            added = early_search(book, vcoins, crit, early_txs, min_early_hits, log, deadline, "verified-early")
            status["verified-early"] = {"ok": True, "wallets": added, "coins": len(vcoins)}
            log(f"✔ verified-early: {added} wallet(s) bought {min_early_hits}+ verified gems early")
        except Exception as exc:
            status["verified-early"] = {"ok": False, "error": str(exc)}
            log(f"✘ verified-early: {exc}")

    coins = None
    if "pump-early" in sources:
        try:
            coins = gem_coins_list(gem_coins, log)
            log(f"… on-chain early-buyer search over {len(coins)} coin(s) (no key needed)")
            added = early_search(book, coins, crit, early_txs, min_early_hits, log, deadline)
            status["pump-early"] = {"ok": True, "wallets": added, "coins": len(coins)}
            log(f"✔ pump-early: {added} wallet(s) bought {min_early_hits}+ big coins early")
        except Exception as exc:
            status["pump-early"] = {"ok": False, "error": str(exc)}
            log(f"✘ pump-early: {exc}")

    if "pump-gems" in sources:
        try:
            if not st_key and not gmgn_key:
                raise SourceError("gem search needs SOLANATRACKER_API_KEY or GMGN_API_KEY "
                                  "(to see who made money on each coin)")
            coins = coins or gem_coins_list(gem_coins, log)
            log(f"… gem search over {len(coins)} coin(s)")
            added = gem_search(book, coins, crit, st_key, gmgn_key, log, deadline)
            status["pump-gems"] = {"ok": True, "wallets": added, "coins": len(coins)}
            log(f"✔ pump-gems: {added} gem hit(s)")
        except Exception as exc:
            status["pump-gems"] = {"ok": False, "error": str(exc)}
            log(f"✘ pump-gems: {exc}")
    return book, status
