"""Solana trading leaderboards: Pump.fun's official PnL board and Kolscan, with history.

`python -m gemtracker board` takes a snapshot, so over days we learn:
  * how much profit a top-5 / top-100 day needs (the target), and
  * which wallets keep coming back on the boards (consistent winners, not one lucky day).
"""
from __future__ import annotations

import html as htmllib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from . import config, net, util

PUMP_BOARD_URL = "https://frontend-api-v3.pump.fun/pnl-leaderboard"
PERIODS = ("daily", "weekly", "monthly")      # Pump.fun windows: rolling 24h, 7d, 30d
LADDER = (1, 5, 10, 20, 50, 100)
HISTORY_FILE = config.DATA_DIR / "leaderboards" / "history.json"
SEEN_FILE = config.DATA_DIR / "leaderboards" / "appearances.json"
DASHBOARD_FILE = config.DOCS_DATA_DIR / "leaderboard.json"
MAX_HISTORY = 3000


@dataclass
class BoardRow:
    board: str            # e.g. "pump.fun daily", "kolscan daily"
    rank: int
    wallet: str
    name: str = ""
    pnl_usd: float = 0.0
    pnl_sol: float = 0.0
    realized_usd: float | None = None
    spent_sol: float | None = None   # SOL put into buys during the window
    roi_pct: float | None = None
    positions: int | None = None     # coins traded during the window
    wins: int | None = None
    losses: int | None = None


def pump_board(period: str, limit: int = 100) -> list:
    data = net.get_json(PUMP_BOARD_URL, params={"period": period, "limit": limit},
                        headers={"Origin": "https://pump.fun", "Referer": "https://pump.fun/"}) or {}
    rows = []
    for e in data.get("entries") or []:
        if not util.is_address(e.get("walletAddress")):
            continue
        rows.append(BoardRow(
            board=f"pump.fun {period}", rank=int(e.get("rank") or len(rows) + 1), wallet=e["walletAddress"],
            name=e.get("username") or e.get("xUsername") or "", pnl_usd=util.num(e.get("pnlUsd")),
            pnl_sol=util.num(e.get("pnlSol")), realized_usd=e.get("realizedPnlUsd"),
            spent_sol=e.get("buySpendSol"), roi_pct=e.get("pnlPercent"), positions=e.get("positionsCount")))
    if not rows:
        raise RuntimeError(f"pump.fun {period} board came back empty")
    return rows


_KOLSCAN_ROW = re.compile(
    r'href="/account/(' + util.ADDRESS_PATTERN + r')\?timeframe=\d+".*?<h1[^>]*>([^<]*)</h1>'
    r'.*?var\(--buy-color\);margin-right:2px">(\d+)</p>/<p[^>]*>(\d+)</p>'
    r'.*?<h1>([+-]?[\d,.]+)<!-- --> <!-- -->Sol</h1><h1>\(<!-- -->\$?([-\d,.]+)<!-- -->\)</h1>', re.S)


def parse_kolscan(page: str) -> list:
    start = page.find('id="S:0"')  # the server-rendered board; earlier markup is the page shell
    rows = []
    for m in _KOLSCAN_ROW.finditer(page[start:] if start >= 0 else page):
        wallet, name, wins, losses, sol, usd = m.groups()
        rows.append(BoardRow(board="kolscan daily", rank=len(rows) + 1, wallet=wallet,
                             name=htmllib.unescape(name).strip(), pnl_sol=float(sol.replace(",", "")),
                             pnl_usd=float(usd.replace(",", "")), wins=int(wins), losses=int(losses)))
    return rows


def kolscan_board() -> list:
    rows = parse_kolscan(net.get_text("https://kolscan.io/leaderboard", headers={"Accept": "text/html"}))
    if not rows:
        raise RuntimeError("no rows found on kolscan.io/leaderboard (page layout changed?)")
    return rows


def ladder(rows: list) -> dict:
    """PnL needed for each milestone rank, e.g. {"5": 47606.0, "100": 4511.0}."""
    by_rank = {r.rank: r.pnl_usd for r in rows}
    return {str(rank): round(by_rank[rank], 2) for rank in LADDER if rank in by_rank}


def take_snapshot(log=print) -> dict:
    boards, errors = {}, {}
    fetchers = [(f"pump.fun {p}", (lambda p=p: pump_board(p))) for p in PERIODS]
    fetchers.append(("kolscan daily", kolscan_board))
    for name, fetch in fetchers:
        try:
            boards[name] = fetch()
            log(f"✔ {name}: {len(boards[name])} rows")
        except Exception as exc:
            errors[name] = str(exc)
            log(f"✘ {name}: {exc}")
    return {"ts": util.now(), "boards": boards, "errors": errors}


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def record(snapshot: dict) -> tuple:
    """Append the snapshot's ladders to history and count each wallet's appearances per day."""
    history = util.load_json(HISTORY_FILE, [])
    history.append({"ts": snapshot["ts"],
                    "ladders": {name: ladder(rows) for name, rows in snapshot["boards"].items()}})
    history = history[-MAX_HISTORY:]

    seen = util.load_json(SEEN_FILE, {})
    day = _day(snapshot["ts"])
    for name, rows in snapshot["boards"].items():
        for r in rows:
            w = seen.setdefault(r.wallet, {"name": "", "days": {}, "best": {}})
            w["name"] = r.name or w["name"]
            days = w["days"].setdefault(name, [])
            if day not in days:
                days.append(day)
            w["best"][name] = min(r.rank, w["best"].get(name, r.rank))
            w["last_seen"] = snapshot["ts"]
    util.save_json(HISTORY_FILE, history)
    util.save_json(SEEN_FILE, seen)
    return history, seen


def repeat_leaders(snapshot: dict, seen: dict, limit: int = 40) -> list:
    """Wallets ranked by how consistently they make the boards.

    Score = distinct (board, day) appearances across all snapshots, plus one point for each
    board the wallet is on right now (daily + weekly + monthly at once = sustained, not a fluke).
    """
    current = {}
    for name, rows in snapshot["boards"].items():
        for r in rows:
            current.setdefault(r.wallet, {})[name] = r
    out = []
    for wallet, info in seen.items():
        appearances = sum(len(days) for days in info.get("days", {}).values())
        now_on = current.get(wallet, {})
        score = appearances + len(now_on)
        if score < 2:
            continue
        best = min(info.get("best", {}).values() or [999])
        daily = now_on.get("pump.fun daily")
        monthly = now_on.get("pump.fun monthly")
        out.append({
            "wallet": wallet, "name": info.get("name") or "", "score": score,
            "boards_now": sorted(now_on), "best_rank": best,
            "days_on_daily_board": len(info.get("days", {}).get("pump.fun daily", [])),
            "pnl_24h_usd": round(daily.pnl_usd, 2) if daily else None,
            "pnl_30d_usd": round(monthly.pnl_usd, 2) if monthly else None,
            "roi_30d_pct": round(monthly.roi_pct, 1) if monthly and monthly.roi_pct is not None else None,
            "spent_30d_sol": round(monthly.spent_sol, 2) if monthly and monthly.spent_sol is not None else None,
        })
    out.sort(key=lambda r: (-r["score"], r["best_rank"]))
    return out[:limit]


def efficient_winners(snapshot: dict, max_spent_sol: float = 25.0, min_roi_pct: float = 300.0,
                      limit: int = 25) -> list:
    """Board entries that made big returns on small money: the closest match to a $100 start."""
    best = {}
    for name, rows in snapshot["boards"].items():
        for r in rows:
            if r.spent_sol is None or r.roi_pct is None:
                continue
            if 0 < r.spent_sol <= max_spent_sol and r.roi_pct >= min_roi_pct:
                if r.wallet not in best or r.roi_pct > best[r.wallet].roi_pct:
                    best[r.wallet] = r
    rows = sorted(best.values(), key=lambda r: -r.roi_pct)[:limit]
    return [asdict(r) for r in rows]


def save_dashboard(snapshot: dict, history: list, seen: dict, top: int = 20) -> dict:
    payload = {
        "updated_at": snapshot["ts"],
        "errors": snapshot["errors"],
        "ladders": {name: ladder(rows) for name, rows in snapshot["boards"].items()},
        "boards": {name: [asdict(r) for r in rows[:top]] for name, rows in snapshot["boards"].items()},
        "history": [{"ts": h["ts"], "pump_daily_5": h["ladders"].get("pump.fun daily", {}).get("5"),
                     "pump_daily_100": h["ladders"].get("pump.fun daily", {}).get("100"),
                     "kolscan_5": h["ladders"].get("kolscan daily", {}).get("5")} for h in history[-500:]],
        "repeat_leaders": repeat_leaders(snapshot, seen),
        "efficient_winners": efficient_winners(snapshot),
    }
    util.save_json(DASHBOARD_FILE, payload, js_var="GEM_LEADERBOARD")
    return payload


def wallet_standing(snapshot: dict, wallet: str) -> list:
    """Where `wallet` sits on each board right now: [(board, rank or None, pnl, cutoff for #5)]."""
    out = []
    for name, rows in snapshot["boards"].items():
        mine = next((r for r in rows if r.wallet == wallet), None)
        cutoff = ladder(rows).get("5")
        out.append((name, mine.rank if mine else None, mine.pnl_usd if mine else None, cutoff,
                    rows[-1].pnl_usd if rows else None))
    return out
