"""Live paper-trading dashboard over the recorder's run directory (a local, read-only page).

    python -m gemtracker.dashboard [--run recorder] [--port 8765] [--open]

Touch data/paper/<run>/DASHBOARD_STOP to shut it down cleanly (it deletes the file on exit).

Serves the page at http://127.0.0.1:<port>/ and its data at /api. Reads only
data/paper/<run>/{config.json,status.json,summary.jsonl,<algo>.jsonl} and the frozen
validation cards in data/research/elite20/cards/<algo>.json. Ledgers are tailed
incrementally, so a poll costs only the lines written since the last one. Binds to localhost
and places nothing: paper only.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from collections import deque
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import DATA_DIR
from .scoreboard import PAPER_DIR, START_USD, TARGET_DAY_USD, add_fill, et_day

DEADLINE = date(2026, 12, 7)        # beat Decu within 2 months (Rahul, 2026-10-07)
RUN_FILES = {"summary.jsonl", "status.json", "config.json"}
RECENT_FILLS = 40
LIVE_SAMPLE_MS = 60_000             # in-memory equity points between the summary.jsonl snapshots
PAGE = Path(__file__).with_name("dashboard.html")
STOP_FILE = "DASHBOARD_STOP"
CARDS_DIR = DATA_DIR / "research" / "elite20" / "cards"
VAL_KEYS = ("days", "trips", "net_return", "geo_daily", "green_days", "max_dd", "win_rate", "latency_ms")


def need_daily_return(start_usd: float, target_day_usd: float, days: int) -> float | None:
    """Smallest constant daily return r with start * (1 + r) ** days * r >= target: fully
    compounded from `start`, the algo earns the target on day `days`."""
    if days <= 0:
        return None
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if start_usd * (1 + mid) ** days * mid >= target_day_usd else (mid, hi)
    return hi


def load_cards(cards_dir: Path) -> dict:
    """Each algo's frozen VAL result (unseen days, live latency, fees in) by algo name."""
    out = {}
    for path in sorted(cards_dir.glob("*.json")):
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):              # caught mid-write: picked up on the next poll
            continue
        val = card.get("val") or {}
        row = {k: val.get(k) for k in VAL_KEYS}
        if isinstance(row["days"], list):
            row["days"] = len(row["days"])
        out[card.get("name") or path.stem] = {**row, "floor_pass": bool(card.get("floor_pass")),
                                              "target_pass": bool(card.get("target_pass"))}
    return out


class Tail:
    """New complete lines of an append-only JSONL file; `reset` is True when the file was rewritten."""

    def __init__(self, path: Path):
        self.path, self.pos = path, 0

    def read(self) -> tuple[bool, list[dict]]:
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return False, []
        reset = size < self.pos
        if reset:
            self.pos = 0
        if size == self.pos:
            return reset, []
        with self.path.open("rb") as fh:
            fh.seek(self.pos)
            chunk = fh.read(size - self.pos)
        end = chunk.rfind(b"\n") + 1          # a half-written last line waits for the next poll
        self.pos += end
        rows = []
        for raw in chunk[:end].splitlines():
            try:
                rows.append(json.loads(raw))
            except ValueError:
                pass
        return reset, rows


class Board:
    """Everything the page shows, brought up to date from the run directory on each poll."""

    def __init__(self, run_dir: Path, cards_dir: Path = CARDS_DIR):
        self.run_dir, self.cards_dir = run_dir, cards_dir
        self.lock = threading.Lock()
        self._reset(None)

    def _reset(self, started):
        self.started = started
        self.ledgers: dict[str, Tail] = {}
        self.days: dict = {}                       # (algo, et_day) -> scoreboard row, this run only
        self.recent: dict[str, deque] = {}
        self.summary = Tail(self.run_dir / "summary.jsonl")
        self.curve: list[tuple[int, dict]] = []    # (t, {algo: equity_usd}) from summary.jsonl
        self.live: deque = deque(maxlen=1440)      # status.json sampled once a minute
        self.status: dict = {}
        self.config: dict = {}

    def _json(self, name: str):
        try:
            return json.loads((self.run_dir / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):              # missing, or caught mid-write: keep the last good one
            return None

    def refresh(self) -> None:
        cfg = self._json("config.json")
        if cfg is not None:
            if cfg.get("started") != self.started:
                self._reset(cfg.get("started"))    # a new run: its ledgers append to the old files
            self.config = cfg
        self.status = self._json("status.json") or self.status
        started = self.started or 0
        for path in sorted(self.run_dir.glob("*.jsonl")):
            if path.name in RUN_FILES:
                continue
            algo = path.stem
            reset, rows = self.ledgers.setdefault(algo, Tail(path)).read()
            if reset:
                self.days = {k: v for k, v in self.days.items() if k[0] != algo}
                self.recent.pop(algo, None)
            for f in rows:
                if f.get("arrival_ms", 0) < started:
                    continue                       # an earlier run's fill in the same ledger
                add_fill(self.days, algo, f)
                self.recent.setdefault(algo, deque(maxlen=RECENT_FILLS)).append(f)
        for snap in self.summary.read()[1]:
            if snap.get("t", 0) >= started:
                self.curve.append((snap["t"], {r["algo"]: r["equity_usd"] for r in snap.get("rows", [])}))
        t = self.status.get("t")
        if t and t >= started and (not self.live or t - self.live[-1][0] >= LIVE_SAMPLE_MS):
            self.live.append((t, self._equities()))

    def _equities(self) -> dict:
        return {a["algo"]: a["equity_usd"] for a in self.status.get("algos", [])}

    def _points(self, start_usd: float) -> list[tuple[int, dict]]:
        pts = [(self.started, {a: start_usd for a in self.config.get("algos", [])})] if self.started else []
        pts += self.curve
        last = pts[-1][0] if pts else 0
        pts += [p for p in self.live if p[0] > last]
        t = self.status.get("t")
        if t and (not pts or t > pts[-1][0]):
            pts.append((t, self._equities()))
        return pts

    def snapshot(self, now_ms: int | None = None) -> dict:
        with self.lock:
            self.refresh()
            return self._build(now_ms or int(time.time() * 1000))

    def _build(self, now_ms: int) -> dict:
        st, cfg = self.status, self.config
        sim = cfg.get("sim", {})
        start_usd = sim.get("start_usd", START_USD)
        sol_usd = st.get("sol_usd") or 0.0
        today = et_day(now_ms)
        points = self._points(start_usd)
        day_open: dict = {}                        # equity at the last point before today's ET midnight
        for t, eq in points:
            if et_day(t) < today:
                day_open.update(eq)
        cards = load_cards(self.cards_dir)
        algos = []
        for a in st.get("algos", []):
            name = a["algo"]
            eq0 = day_open.get(name, start_usd)    # a run that began today opened at the start stake
            d = self.days.get((name, today), {})
            day_pnl = a["equity_usd"] - eq0
            algos.append({**a, "baseline": name.startswith("base_"),
                          "day_open_usd": round(eq0, 2), "day_pnl_usd": round(day_pnl, 2),
                          "day_return": round(day_pnl / eq0, 4) if eq0 else None,
                          "day_realized_usd": round(d.get("pnl_usd", 0.0), 2),
                          "day_trips": d.get("trips", 0), "day_wins": d.get("wins", 0),
                          "fees_usd": round((a.get("venue_fees_sol", 0.0) + a.get("tx_fees_sol", 0.0)) * sol_usd, 2),
                          "val": cards.get(name)})
        algos.sort(key=lambda r: -r["equity_usd"])
        fills = []
        for base in (False, True):                 # the busy baselines must not crowd out the algos
            fills += sorted(((algo, f) for algo, q in self.recent.items() if algo.startswith("base_") == base
                             for f in q), key=lambda p: -p[1]["arrival_ms"])[:RECENT_FILLS]
        fills.sort(key=lambda p: -p[1]["arrival_ms"])
        recent = [{"t": f["arrival_ms"], "algo": algo, "baseline": algo.startswith("base_"),
                   "side": f.get("side"), "status": f.get("status"),
                   "reason": f.get("reason", ""), "why": f.get("why", ""), "sol": f.get("sol", 0.0),
                   "mcap_sol": f.get("mcap_sol"), "pnl_sol": f.get("pnl_sol", 0.0),
                   "pnl_usd": round(f.get("pnl_sol", 0.0) * (f.get("sol_usd") or 0.0), 2),
                   "venue": f.get("venue"), "mint": f.get("mint")} for algo, f in fills]
        days_left = (DEADLINE - today).days
        return {"now": now_ms, "today": today.isoformat(), "target_day_usd": TARGET_DAY_USD,
                "deadline": DEADLINE.isoformat(), "days_left": days_left, "start_usd": start_usd,
                "need_daily_return": need_daily_return(start_usd, TARGET_DAY_USD, days_left),
                "run": {"name": self.run_dir.name, "started": self.started, "commit": cfg.get("commit"),
                        "latency_ms": sim.get("latency_ms"), "venue_latency_ms": sim.get("venue_latency_ms", {}),
                        "paper_only": cfg.get("paper_only", True)},
                "health": {k: st.get(k) for k in ("t", "uptime_min", "queue", "tokens", "pools_known", "parked",
                                                  "resolver_failures", "feed_lag_ms", "loop_ms", "sol_usd")},
                "algos": algos,
                "validated": sum(1 for a in algos if not a["baseline"] and (a["val"] or {}).get("floor_pass")),
                "curve": {"t": [t for t, _ in points],
                          "series": {a["algo"]: [eq.get(a["algo"]) for _, eq in points] for a in algos}},
                "recent": recent}


def make_server(board: Board, port: int, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if (self.headers.get("Host") or "").rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"):
                self.send_error(403)               # DNS-rebinding guard: only a page on this machine reads it
                return
            path = self.path.split("?", 1)[0]
            if path == "/api":
                body, ctype = json.dumps(board.snapshot()).encode(), "application/json"
            elif path in ("/", "/index.html"):
                body, ctype = PAGE.read_bytes(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):              # quiet: the page polls every few seconds
            pass

    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    return srv


def watch_stop(srv: ThreadingHTTPServer, stop: Path, every_s: float = 2.0) -> None:
    """Shut the server down once `stop` appears, then remove it (a restart needs no process kill)."""
    while not stop.exists():
        time.sleep(every_s)
    srv.shutdown()
    stop.unlink(missing_ok=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Live paper-trading dashboard (localhost, read-only)")
    ap.add_argument("--run", default="recorder", help="run directory under data/paper/")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    args = ap.parse_args(argv)
    run_dir = PAPER_DIR / args.run
    srv = make_server(Board(run_dir), args.port)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"dashboard {url} over {run_dir}", flush=True)
    if args.open:
        import webbrowser
        webbrowser.open(url)
    threading.Thread(target=watch_stop, args=(srv, run_dir / STOP_FILE), daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
