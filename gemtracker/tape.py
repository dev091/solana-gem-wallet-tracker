"""Append-only record of everything the live runner saw (the "tape").

Rows are JSON lines in hourly gzip files: data/tape/YYYYMMDD/HH.jsonl.gz (UTC hour).
Every row carries the clocks separately, so a replay never uses information before it
arrived:  slot / ts = chain clock,  rx = local receive time in ms.
When an hour closes, its SHA-256 and row count go into data/tape/manifest.jsonl so the
evidence can be checked later. Replays read the same files back in order.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import time
from pathlib import Path

from .config import DATA_DIR

TAPE_DIR = DATA_DIR / "tape"


def event_row(ev, rx_ms: int) -> dict:
    """Compact dict for one ChainEvent; empty fields are dropped."""
    row = {"rx": rx_ms, "k": ev.kind, "v": ev.venue, "sig": ev.signature, "i": ev.index,
           "slot": ev.slot, "ts": ev.ts, "mint": ev.mint, "pool": ev.pool, "u": ev.user,
           "side": ev.side, "q": ev.quote, "t": ev.tokens, "rq": ev.reserve_quote,
           "rb": ev.reserve_base, "fee": ev.fee_bps, "pg": round(ev.progress, 5),
           "px": ev.price}
    if ev.quote_mint and ev.quote_mint != "So11111111111111111111111111111111111111112":
        row["qm"] = ev.quote_mint
    if ev.extra:
        row["x"] = ev.extra
    return {k: v for k, v in row.items() if v not in ("", 0, 0.0, None, {})}


class TapeWriter:
    def __init__(self, root: Path = TAPE_DIR):
        self.root = Path(root)
        self._hour = None
        self._fh = None
        self._path = None
        self.rows = 0

    def _open(self, hour: int):
        self.close()
        stamp = time.strftime("%Y%m%d/%H", time.gmtime(hour * 3600))
        self._path = self.root / f"{stamp}.jsonl.gz"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = gzip.open(self._path, "at", encoding="utf-8")
        self._hour, self.rows = hour, 0

    def write(self, row: dict) -> None:
        hour = int(row.get("rx", time.time() * 1000) // 3_600_000)
        if hour != self._hour:
            self._open(hour)
        self._fh.write(json.dumps(row, separators=(",", ":")) + "\n")
        self.rows += 1

    def flush(self) -> None:
        if self._fh:
            self._fh.flush()

    def close(self) -> None:
        if not self._fh:
            return
        self._fh.close()
        digest = hashlib.sha256(self._path.read_bytes()).hexdigest()
        with open(self.root / "manifest.jsonl", "a", encoding="utf-8") as m:
            m.write(json.dumps({"file": self._path.relative_to(self.root).as_posix(),
                                "rows_this_session": self.rows, "sha256": digest,
                                "closed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                    + "\n")
        self._fh = None


def read_tape(root: Path = TAPE_DIR, start: str = "", end: str = ""):
    """Yield rows from every hour file in order; start/end are 'YYYYMMDD/HH' bounds."""
    for path in sorted(Path(root).glob("*/*.jsonl.gz")):
        key = path.relative_to(root).as_posix()[:11]
        if (start and key < start) or (end and key > end):
            continue
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:  # half-written last line of the live hour
                        break
                    yield row
        except (EOFError, OSError):  # the hour being written right now ends mid-block
            continue
