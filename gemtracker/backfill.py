"""Turn free downloaded pump.fun history into replayable tapes.

    python -m gemtracker.backfill --source slinky21|jocry [--from YYYY-MM-DD --to YYYY-MM-DD]

Each US-Eastern day becomes one tape, `<root>/<source>/<YYYYMMDD>/day.jsonl.gz`, plus a
`manifest.json` next to it. That is the live layout one level up (`<day>/<file>.jsonl.gz`),
so `tape.read_tape(root / source, "20260810", "20260810/~")` reads one day (it loads the
whole file; `iter_day` streams it). The rows are built with the live `tape.event_row`, so they have the
same shape as what the recorder writes: create / trade on venue "pump", and a graduation
as the live pair `migrate` (pump) + `pool` (pumpswap).

Where the tapes go (Jane Street rule: one holdout nobody looks at):
    DEV      data/tapes/hist/<source>/          jocry, and Slinky21 up to 2026-09-04 ET
    HOLDOUT  data/tapes/hist_holdout/<source>/  Slinky21 from 2026-09-05 ET (no replay, no stats)

Time. The datasets carry block time (Slinky21, whole seconds) or a websocket timestamp
(jocry), not our receive time. Slinky21: rows are ordered by (slot, tx_index); chain_ms
spreads the slots seen within one block-time second evenly over that second (slots are
~400 ms), and a running max keeps it monotone. jocry has no slot, so its timestamp is
used as chain_ms (a proxy). rx = chain_ms + lag (default 1400 ms, the live feed's typical
delay), so the algos see each row about as late as they would live.

Not in these tapes: PumpSwap trades after a coin migrates. Algos that trade migrated
coins (frank_degods, decu's post-migration mode) cannot be tested on them.

Streaming: Slinky21 is read one UTC hour at a time with iter_batches over the parquet row
groups whose block-time range overlaps that hour. jocry's trade files are sorted by mint,
so one pass spills them into per-day parquet parts first. Memory stays bounded.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import shutil
import time
from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .chain_events import PUMP_INITIAL_REAL_TOKENS, WSOL, ChainEvent, _price
from .config import DATA_DIR
from .scoreboard import et_day
from .tape import event_row

HF_DIR = DATA_DIR / "history" / "hf"
SLINKY_DIR = HF_DIR / "Slinky21" / "Pumpfun_v2_dataset"
JOCRY_DIR = HF_DIR / "jocry" / "Pumpfun_Memecoin_Corpus"
DEV_ROOT = DATA_DIR / "tapes" / "hist"
HOLDOUT_ROOT = DATA_DIR / "tapes" / "hist_holdout"
SPILL_ROOT = DATA_DIR / "tapes" / "_spill"
HOLDOUT_FROM = date(2026, 9, 5)       # Slinky21 days from here on are holdout
DEFAULT_LAG_MS = 1400

PUMP_V_SOL = 30_000_000_000           # initial virtual SOL of a SOL-quoted pump curve
PUMP_V_TOKENS = 1_073_000_000_000_000
PUMP_FEE_BPS = 125                    # 95 protocol + 30 creator: jocry has no fee field
K_PUMP = PUMP_V_SOL * PUMP_V_TOKENS
MAYHEM_V_TOKENS = 2_073_000_000_000_000  # jocry: mayhem coins mint 2B tokens (KNOWN_ISSUES 1.1)
K_MAYHEM = PUMP_V_SOL * MAYHEM_V_TOKENS
K_TOL = 0.03                          # curve state within 3% of the pump invariant is consistent
FILL_TOL = (0.5, 2.0)                 # a fill vs the curve's own quote for that size
NON_SOL = "?"                         # quote mint not in the data: anything but WSOL
POOL_SENTINELS = ("synthetic_graduation_queue", "backfilled_from_pumpswap_trade")
KIND_RANK = {"create": 0, "trade": 1, "graduate": 2, "migrate": 2, "pool": 3}

NO_PUMPSWAP_NOTE = ("no post-migration PumpSwap trades: the source covers the pump.fun bonding "
                    "curve only, so frank_degods and decu's post-migration mode cannot be tested")


# ---------------------------------------------------------------- shared helpers

def et_bounds(day: date) -> tuple[int, int]:
    """UTC epoch-ms [start, end) of one US-Eastern day."""
    def start_of(d: date) -> int:
        midnight = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
        for off in (4, 5):
            t = midnight + off * 3_600_000
            if et_day(t) == d and et_day(t - 1) != d:
                return t
        raise ValueError(day)
    return start_of(day), start_of(day + timedelta(days=1))


def split_of(source: str, day: date) -> str:
    return "holdout" if source == "slinky21" and day >= HOLDOUT_FROM else "dev"


def root_of(split: str) -> Path:
    return HOLDOUT_ROOT if split == "holdout" else DEV_ROOT


def tape_path(root: Path, source: str, day: date) -> Path:
    return Path(root) / source / day.strftime("%Y%m%d") / "day.jsonl.gz"


def daterange(a: date, b: date):
    while a <= b:
        yield a
        a += timedelta(days=1)


def pump_progress(vb: float, mayhem: bool = False) -> float:
    """Share of the curve's sellable tokens already bought, from virtual token reserves."""
    init, real = (MAYHEM_V_TOKENS, 2 * PUMP_INITIAL_REAL_TOKENS) if mayhem else \
        (PUMP_V_TOKENS, PUMP_INITIAL_REAL_TOKENS)
    return max(0.0, min(1.0, (init - vb) / real))


class DayWriter:
    """One ET day's tape: rows in rx order, then a manifest. Written to a temp name first."""

    def __init__(self, path: Path, lag_ms: int):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tmp = self.path.with_suffix(".tmp")
        self.fh = gzip.open(self.tmp, "wt", encoding="utf-8", compresslevel=5)
        self.lag_ms = lag_ms
        self.rows = 0
        self.kinds = Counter()
        self.last_rx = None
        self.first_rx = None
        self.out_of_order = 0

    def write(self, ev: ChainEvent, chain_ms: int) -> None:
        rx = int(chain_ms) + self.lag_ms
        if self.last_rx is not None and rx < self.last_rx:
            self.out_of_order += 1
        self.first_rx = rx if self.first_rx is None else self.first_rx
        self.last_rx = rx
        self.fh.write(json.dumps(event_row(ev, rx), separators=(",", ":")) + "\n")
        self.rows += 1
        self.kinds[ev.kind] += 1

    def close(self, manifest: dict) -> dict:
        self.fh.close()
        h = hashlib.sha256()
        with open(self.tmp, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        sha = h.hexdigest()
        os.replace(self.tmp, self.path)
        manifest = dict(manifest, rows=self.rows, rows_by_kind=dict(self.kinds),
                        lag_ms=self.lag_ms, first_rx=self.first_rx, last_rx=self.last_rx,
                        rx_out_of_order=self.out_of_order, file=self.path.name, sha256=sha,
                        no_pumpswap=NO_PUMPSWAP_NOTE,
                        written=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        (self.path.parent / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                                        encoding="utf-8")
        return manifest


def order_tx_trades(group: list) -> list:
    """Several trades of one coin inside one transaction: chain them by curve state
    (each trade's pre-trade token reserve is the previous trade's post-trade reserve).
    `group` holds (seq, side, tokens, vb_after); returns them in execution order, or in
    their original order when they do not chain."""
    if len(group) < 2:
        return group
    pre = {}
    for g in group:
        _, side, tok, vb = g
        pre.setdefault(vb + tok if side == "buy" else vb - tok, []).append(g)
    posts = {g[3] for g in group}
    heads = [g for g in group if (g[3] + g[2] if g[1] == "buy" else g[3] - g[2]) not in posts]
    if len(heads) != 1:
        return sorted(group)
    out, cur, used = [heads[0]], heads[0], {heads[0][0]}
    while len(out) < len(group):
        nxt = [g for g in pre.get(cur[3], []) if g[0] not in used]
        if not nxt:
            return sorted(group)
        cur = nxt[0]
        used.add(cur[0])
        out.append(cur)
    return out


# ---------------------------------------------------------------- Slinky21

SLINKY_COLS = {
    "create": ["block_time", "slot", "tx_index", "signature", "mint", "bonding_curve", "creator",
               "tx_signer", "token_name", "symbol", "is_mayhem_mode", "token_total_supply",
               "virtual_sol_reserves", "virtual_token_reserves"],
    "trade": ["block_time", "slot", "tx_index", "signature", "mint", "trade_user", "creator",
              "ix_name", "sol_amount", "token_amount", "virtual_sol_reserves",
              "virtual_token_reserves", "real_sol_reserves", "real_token_reserves",
              "fee_basis_points", "creator_fee_basis_points"],
    "graduate": ["block_time", "slot", "tx_index", "signature", "mint", "pool", "triggered_by",
                 "mint_amount", "sol_amount"],
}
REQUIRED = {"create": ["slot", "signature", "mint", "virtual_sol_reserves", "virtual_token_reserves"],
            "trade": ["slot", "signature", "mint", "ix_name", "sol_amount", "token_amount",
                      "virtual_sol_reserves", "virtual_token_reserves", "real_sol_reserves",
                      "real_token_reserves"],
            "graduate": ["slot", "signature", "mint"]}
NO_TX_INDEX = 1_000_000_000  # missing tx_index (~0.1% of rows): ordered last in their slot
DEDUPE = {"create": ["signature", "mint"], "graduate": ["signature", "mint"],
          "trade": ["signature", "mint", "ix_name", "sol_amount", "token_amount"]}


class SlinkyIndex:
    """Every parquet row group with its block-time range, read from file metadata only."""

    def __init__(self, base: Path = SLINKY_DIR, stable_s: float = 120.0):
        import pyarrow.parquet as pq
        self.pq = pq
        self.groups = {k: [] for k in SLINKY_COLS}   # kind -> [(path, rg, tmin_us, tmax_us)]
        self.skipped = []
        now = time.time()
        for kind in SLINKY_COLS:
            for path in sorted(Path(base).glob(f"*/*/{kind}/*.parquet")):
                if now - path.stat().st_mtime < stable_s:  # may still be downloading
                    self.skipped.append(str(path))
                    continue
                try:
                    meta = pq.ParquetFile(path).metadata
                except Exception:
                    self.skipped.append(str(path))
                    continue
                col = meta.schema.to_arrow_schema().get_field_index("block_time")
                for i in range(meta.num_row_groups):
                    st = meta.row_group(i).column(col).statistics
                    lo, hi = (_us(st.min), _us(st.max)) if st is not None and st.has_min_max \
                        else (0, 2 ** 62)
                    self.groups[kind].append((path, i, lo, hi))
        self._files = OrderedDict()

    def _pf(self, path):
        pf = self._files.pop(path, None) or self.pq.ParquetFile(path)
        self._files[path] = pf
        while len(self._files) > 8:
            self._files.popitem(last=False)
        return pf

    def span_ms(self) -> tuple[int, int]:
        allg = [g for gs in self.groups.values() for g in gs]
        return min(g[2] for g in allg) // 1000, max(g[3] for g in allg) // 1000

    def read(self, kind: str, t0_ms: int, t1_ms: int):
        """Rows of `kind` with block_time in [t0, t1), as a pandas frame (with `seq`)."""
        import pandas as pd
        import pyarrow as pa
        import pyarrow.compute as pc
        lo, hi = t0_ms * 1000, t1_ms * 1000
        parts, files = [], set()
        for path, rg, gmin, gmax in self.groups[kind]:
            if gmax < lo or gmin >= hi:
                continue
            files.add(path.name)
            for batch in self._pf(path).iter_batches(batch_size=65_536, row_groups=[rg],
                                                     columns=SLINKY_COLS[kind]):
                bt = batch.column("block_time").cast(pa.int64())
                mask = pc.and_(pc.greater_equal(bt, lo), pc.less(bt, hi))
                if pc.any(mask).as_py():
                    parts.append(batch.filter(mask))
        if not parts:
            return pd.DataFrame(columns=SLINKY_COLS[kind] + ["seq"]), files
        # files differ in int widths (tx_index int32 in some, int64 in others)
        table = pa.concat_tables([pa.Table.from_batches([b]) for b in parts],
                                 promote_options="permissive")
        table = table.set_column(0, "block_time", table.column("block_time").cast(pa.int64()))
        df = table.to_pandas()
        df["seq"] = range(len(df))
        return df, files


def _i(v) -> int:
    """int of a parquet value that may be null (None, or NaN after a pandas concat)."""
    return 0 if v is None or v != v else int(v)


def _s(v) -> str:
    return v if isinstance(v, str) else ""


def _us(v) -> int:
    if isinstance(v, datetime):
        return int(v.timestamp() * 1_000_000)
    return int(v)


def slinky_chain_ms(bt_us, slots) -> list:
    """Per row: block-time second plus the slot's even share of that second."""
    import numpy as np
    import pandas as pd
    sec = (np.asarray(bt_us, dtype="int64") // 1_000_000)
    slots = np.asarray(slots, dtype="int64")
    d = pd.DataFrame({"sec": sec, "slot": slots})
    g = d.groupby("sec")["slot"]
    lo, hi = g.transform("min").to_numpy(), g.transform("max").to_numpy()
    frac = (slots - lo) / (hi - lo + 1)
    return (sec * 1000 + np.floor(frac * 1000)).astype("int64")


def convert_slinky_day(day: date, index: SlinkyIndex, out_root: Path | None = None,
                       lag_ms: int = DEFAULT_LAG_MS, state: dict | None = None) -> dict:
    """Write one ET day of Slinky21. `state` carries per-coin facts between days."""
    import numpy as np
    import pandas as pd
    state = state if state is not None else {}
    mayhem = state.setdefault("mayhem", OrderedDict())    # mint -> bool, from creates
    sol_quoted = state.setdefault("sol_quoted", OrderedDict())
    split = split_of("slinky21", day)
    out_root = Path(out_root) if out_root is not None else root_of(split)
    t0, t1 = et_bounds(day)
    writer = DayWriter(tape_path(out_root, "slinky21", day), lag_ms)
    drops, inputs, raw, flags = Counter(), set(), Counter(), Counter()
    last_chain = 0
    for h0 in range(t0, t1, 3_600_000):
        frames = []
        for kind in ("create", "trade", "graduate"):
            df, files = index.read(kind, h0, min(h0 + 3_600_000, t1))
            inputs |= files
            raw[kind] += len(df)
            if len(df):
                before = len(df)
                df = df.drop_duplicates(DEDUPE[kind])
                drops[f"duplicate_{kind}"] += before - len(df)
                need = df[REQUIRED[kind]].notna().all(axis=1)
                drops[f"{kind}_missing_fields"] += int((~need).sum())
                df = df[need]
            df["kind"] = kind
            frames.append(df)
        df = pd.concat([f for f in frames if len(f)], ignore_index=True) if any(
            len(f) for f in frames) else None
        if df is None:
            continue
        df["krank"] = df["kind"].map(KIND_RANK)
        no_tx = df["tx_index"].isna()
        flags["tx_index_missing_ordered_last_in_slot"] += int(no_tx.sum())
        df["tx_index"] = df["tx_index"].fillna(NO_TX_INDEX).astype("int64")
        df["seq"] = np.arange(len(df))
        df.sort_values(["slot", "tx_index", "krank", "seq"], inplace=True, kind="stable")
        df["chain"] = slinky_chain_ms(df["block_time"].to_numpy(), df["slot"].to_numpy())
        chain = np.maximum.accumulate(np.maximum(df["chain"].to_numpy(), last_chain))
        df["chain"] = chain
        last_chain = int(chain[-1])
        last_chain = _emit_slinky(df, writer, drops, mayhem, sol_quoted, last_chain)
        for d in (mayhem, sol_quoted):
            while len(d) > 400_000:
                d.popitem(last=False)
    manifest = {"source": "slinky21", "day": day.isoformat(), "split": split,
                "utc_window_ms": [t0, t1], "raw_rows": dict(raw), "dropped": {k: v for k, v in drops.items() if v},
                "flagged": dict(flags), "inputs": sorted(inputs),
                "chain_ms": "block_time second + even share of that second by slot rank; "
                            "running max",
                "notes": ["non-SOL-quoted coins (virtual_sol - real_sol != 30 SOL) carry "
                          "qm '?' and 6-decimal quote prices; quote mint not in the data",
                          "pool rows: rq/rb from the graduate event's sol/mint amounts",
                          "trade i = tx_index (the data has no event index)"]}
    if index.skipped:
        manifest["skipped_unstable_files"] = len(index.skipped)
    return writer.close(manifest)


def _emit_slinky(df, writer, drops, mayhem, sol_quoted, last_chain) -> int:
    cols = {c: df[c].tolist() for c in df.columns}
    n = len(df)
    kinds = cols["kind"]
    # trades of one coin sharing a transaction: execution order from the curve chain
    order = list(range(n))
    trade_pos = {}
    for j in range(n):
        if kinds[j] == "trade":
            trade_pos.setdefault((cols["slot"][j], cols["tx_index"][j], cols["mint"][j]), []).append(j)
    for key, js in trade_pos.items():
        if len(js) < 2:
            continue
        group = [(j, "buy" if cols["ix_name"][j].startswith("buy") else "sell",
                  int(cols["token_amount"][j]), int(cols["virtual_token_reserves"][j])) for j in js]
        for slot_j, g in zip(sorted(js), order_tx_trades(group)):
            order[slot_j] = g[0]
    for j in order:
        kind, ts = kinds[j], int(cols["block_time"][j]) // 1_000_000
        chain = cols["chain"][j]
        base = dict(signature=cols["signature"][j], index=int(cols["tx_index"][j]) % NO_TX_INDEX,
                    slot=int(cols["slot"][j]), ts=ts, mint=cols["mint"][j])
        if kind == "create":
            vq, vb = int(cols["virtual_sol_reserves"][j]), int(cols["virtual_token_reserves"][j])
            sol = vq == PUMP_V_SOL
            mm = bool(cols["is_mayhem_mode"][j])
            mayhem[base["mint"]] = mm
            sol_quoted[base["mint"]] = sol
            writer.write(ChainEvent(
                "create", "pump", user=_s(cols["tx_signer"][j]) or _s(cols["creator"][j]),
                price=_price(vq, vb, 9 if sol else 6), quote_mint=WSOL if sol else NON_SOL,
                reserve_quote=vq, reserve_base=vb,
                extra={"name": _s(cols["token_name"][j])[:64],
                       "symbol": _s(cols["symbol"][j])[:32], "creator": _s(cols["creator"][j]),
                       "bonding_curve": _s(cols["bonding_curve"][j]),
                       "supply": _i(cols["token_total_supply"][j]) // 10 ** 6, "mayhem": mm},
                **base), chain)
        elif kind == "trade":
            vq, vb = int(cols["virtual_sol_reserves"][j]), int(cols["virtual_token_reserves"][j])
            rs = int(cols["real_sol_reserves"][j])
            if vq <= 0 or vb <= 0:
                drops["non_sol_no_quote_fields"] += 1  # non-SOL coin: quote fields absent
                continue
            ix = cols["ix_name"][j] or ""
            if not ix.startswith(("buy", "sell")):
                drops["trade_unknown_ix"] += 1
                continue
            sol = vq - rs == PUMP_V_SOL
            sol_quoted[base["mint"]] = sol
            fee = _i(cols["fee_basis_points"][j]) + _i(cols["creator_fee_basis_points"][j])
            pg = 1 - int(cols["real_token_reserves"][j]) / PUMP_INITIAL_REAL_TOKENS
            writer.write(ChainEvent(
                "trade", "pump", user=_s(cols["trade_user"][j]),
                side="buy" if ix.startswith("buy") else "sell", quote=int(cols["sol_amount"][j]),
                tokens=int(cols["token_amount"][j]), price=_price(vq, vb, 9 if sol else 6),
                quote_mint=WSOL if sol else NON_SOL, reserve_quote=vq, reserve_base=vb,
                fee_bps=fee, progress=max(0.0, min(1.0, pg)),
                extra={"creator": _s(cols["creator"][j]),
                       "mayhem": bool(mayhem.get(base["mint"], False))}, **base), chain)
        else:  # graduate -> the live pair: migrate (pump) + pool (pumpswap)
            mint = base["mint"]
            sq, mt = _i(cols["sol_amount"][j]), _i(cols["mint_amount"][j])
            sol = sol_quoted.get(mint, sq >= 10 * 10 ** 9)
            writer.write(ChainEvent("migrate", "pump", user=_s(cols["triggered_by"][j]),
                                    progress=1.0, **base), chain)
            writer.write(ChainEvent("pool", "pumpswap", pool=_s(cols["pool"][j]),
                                    quote_mint=WSOL if sol else NON_SOL, reserve_quote=sq,
                                    reserve_base=mt, price=_price(sq, mt, 9 if sol else 6),
                                    extra={"base_decimals": 6}, **base), chain)
        last_chain = max(last_chain, chain)
    return last_chain


# ---------------------------------------------------------------- jocry

JOCRY_TRADE_COLS = ["id", "mint", "tx_signature", "event_time", "is_buy", "sol_amount",
                    "token_amount", "user_wallet", "v_tokens_bonding_curve",
                    "v_sol_bonding_curve", "price_sol"]


def _et_day_keys(ms):
    """Vectorised scoreboard.et_day for epoch-ms arrays -> int YYYYMMDD."""
    import numpy as np
    import pandas as pd
    ms = np.asarray(ms, dtype="int64")
    out = np.empty(len(ms), dtype="int64")
    years = pd.to_datetime(ms, unit="ms").year.to_numpy()
    for y in np.unique(years):
        a = int(datetime(y, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
        s = next(d for d in (a + i * 86_400_000 for i in range(31))
                 if datetime.fromtimestamp(d / 1000, timezone.utc).weekday() == 6) + 7 * 86_400_000 + 7 * 3_600_000
        b = int(datetime(y, 11, 1, tzinfo=timezone.utc).timestamp() * 1000)
        e = next(d for d in (b + i * 86_400_000 for i in range(31))
                 if datetime.fromtimestamp(d / 1000, timezone.utc).weekday() == 6) + 6 * 3_600_000
        m = years == y
        off = np.where((ms[m] >= s) & (ms[m] < e), 4, 5) * 3_600_000
        local = pd.to_datetime(ms[m] - off, unit="ms")
        out[m] = local.year * 10000 + local.month * 100 + local.day
    return out


def jocry_spill(base: Path = JOCRY_DIR, spill: Path = SPILL_ROOT / "jocry",
                days: set | None = None) -> dict:
    """Pass 1: re-bucket the mint-sorted trade files into per-ET-day parquet parts."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    spill = Path(spill)
    counts = Counter()
    for path in sorted((Path(base) / "trades").glob("*.parquet")):
        done = spill / f".done-{path.stem}"
        if done.exists():
            continue
        writers = {}
        for batch in pq.ParquetFile(path).iter_batches(batch_size=200_000, columns=JOCRY_TRADE_COLS):
            et = batch.column("event_time").cast(pa.timestamp("us", tz="UTC")).cast(pa.int64())
            ms = pc.divide(et, 1000).to_numpy(zero_copy_only=False)
            keys = _et_day_keys(ms)
            batch = batch.set_column(batch.schema.get_field_index("event_time"), "event_time",
                                     pa.array(ms, pa.int64()))
            for k in set(keys.tolist()):
                if days is not None and k not in days:
                    continue
                part = batch.filter(pa.array(keys == k))
                w = writers.get(k)
                if w is None:
                    (spill / str(k)).mkdir(parents=True, exist_ok=True)
                    w = writers[k] = pq.ParquetWriter(spill / str(k) / f"{path.stem}.parquet",
                                                      part.schema)
                w.write_batch(part)
                counts[k] += part.num_rows
        for w in writers.values():
            w.close()
        done.write_text("ok")
    return dict(counts)


def jocry_clean(df) -> tuple:
    """Reconcile one frame of jocry trades with the pump curve (KNOWN_ISSUES: sol_amount and
    reserves are not always consistent). Price and reserves come from the curve state:

      * reserves on the pump invariant (vq*vb within 3% of 30 SOL x 1.073B tokens, or the
        mayhem 2.073B curve) are used as they are;
      * otherwise, when price_sol agrees with the trade's own fill (sol/tokens within 0.5-2x),
        the reserves are rebuilt on the coin's pump curve at that price (`curve_rebuilt`);
      * anything else has no usable curve state and is dropped;
      * sol_amount missing, or off by more than 2x from what the curve pays for that many
        tokens, is replaced by the curve's amount (`q_from_curve`).

    `df` needs JOCRY_TRADE_COLS plus a `mayhem` column. Returns (kept frame with vq, vb, q, t
    integer columns, Counter of drops, Counter of repairs)."""
    import numpy as np
    drops, fixes = Counter(), Counter()
    n0 = len(df)
    tok = df["token_amount"].to_numpy(dtype="float64")
    bad_tok = ~(tok > 0)
    if bad_tok.any():
        drops["no_token_amount"] += int(bad_tok.sum())
        df = df[~bad_tok]
    vq = df["v_sol_bonding_curve"].to_numpy(dtype="float64")
    vb = df["v_tokens_bonding_curve"].to_numpy(dtype="float64")
    px = df["price_sol"].to_numpy(dtype="float64") * 1000  # lamports per micro-token
    sol = df["sol_amount"].to_numpy(dtype="float64") * 1e9
    tok = df["token_amount"].to_numpy(dtype="float64") * 1e6
    mayhem = df["mayhem"].to_numpy(dtype=bool)
    buy = df["is_buy"].to_numpy(dtype=bool)
    K = np.where(mayhem, float(K_MAYHEM), float(K_PUMP))
    with np.errstate(invalid="ignore", divide="ignore"):
        on_curve = np.abs(vq * vb / K - 1) < K_TOL
        fill = sol / tok / px
        price_ok = np.isfinite(px) & (px > 0) & (fill >= FILL_TOL[0]) & (fill <= FILL_TOL[1])
        rebuild = ~on_curve & price_ok
        vq2 = np.where(on_curve, vq, np.sqrt(K * px))
        vb2 = np.where(on_curve, vb, np.sqrt(K / px))
    keep = on_curve | rebuild
    drops["no_consistent_curve_state"] += int((~keep).sum())
    fixes["curve_rebuilt"] += int(rebuild.sum())
    with np.errstate(invalid="ignore", divide="ignore"):
        pre_vb = np.where(buy, vb2 + tok, vb2 - tok)          # reserves are post-trade
        pre_vq = vq2 * vb2 / pre_vb                       # the row's own invariant
        q_curve = np.abs(vq2 - pre_vq)
        ratio = sol / q_curve
        q_bad = ~((ratio >= FILL_TOL[0]) & (ratio <= FILL_TOL[1]))
    q = np.where(q_bad, q_curve, sol)
    fixes["q_from_curve"] += int((keep & q_bad).sum())
    out = df.assign(vq=np.rint(vq2), vb=np.rint(vb2), q=np.rint(q), t=np.rint(tok))[keep]
    out = out[np.isfinite(out["vq"]) & (out["vb"] > 0) & np.isfinite(out["q"])]
    drops["no_consistent_curve_state"] += int(keep.sum()) - len(out)
    for c in ("vq", "vb", "q", "t"):
        out[c] = out[c].astype("int64")
    assert len(out) + sum(drops.values()) == n0
    return out, drops, fixes


class JocryMeta:
    """tokens.parquet and migrations.parquet, held as small frames indexed by ET day."""

    def __init__(self, base: Path = JOCRY_DIR):
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        cols = ["mint", "detected_at", "name", "symbol", "is_mayhem_mode", "creator",
                "bonding_curve_key"]
        tok = pq.read_table(Path(base) / "tokens.parquet", columns=cols)
        tok = tok.set_column(1, "detected_at", tok.column("detected_at")
                             .cast(pa.timestamp("us", tz="UTC")).cast(pa.int64()))
        self.tokens = tok.to_pandas()
        self.tokens["ms"] = self.tokens["detected_at"] // 1000
        self.tokens["mayhem"] = self.tokens["is_mayhem_mode"].fillna(False).astype(bool)
        self.tokens["day"] = _et_day_keys(self.tokens["ms"].to_numpy())
        mig = pq.read_table(Path(base) / "migrations.parquet")
        mig = mig.set_column(1, "migrated_at", mig.column("migrated_at")
                             .cast(pa.timestamp("us", tz="UTC")).cast(pa.int64()))
        self.migrations = mig.to_pandas()
        self.migrations["ms"] = self.migrations["migrated_at"] // 1000
        self.migrations["day"] = _et_day_keys(self.migrations["ms"].to_numpy())
        self.by_mint = self.tokens.set_index("mint")[["creator", "mayhem"]]


def convert_jocry_day(day: date, meta: JocryMeta, spill: Path = SPILL_ROOT / "jocry",
                      out_root: Path | None = None, lag_ms: int = DEFAULT_LAG_MS) -> dict:
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    key = int(day.strftime("%Y%m%d"))
    parts = sorted((Path(spill) / str(key)).glob("*.parquet"))
    trades = pd.concat([pq.read_table(p).to_pandas() for p in parts], ignore_index=True) \
        if parts else pd.DataFrame(columns=JOCRY_TRADE_COLS)
    raw = len(trades)
    drops, fixes = Counter(), Counter()
    before = len(trades)
    trades = trades.drop_duplicates(["tx_signature", "mint", "is_buy", "sol_amount", "token_amount"])
    drops["duplicate_trade"] = before - len(trades)
    trades = trades.join(meta.by_mint, on="mint")
    drops["trade_unknown_mint"] = int(trades["mayhem"].isna().sum())
    trades = trades[trades["mayhem"].notna()].copy()
    trades["mayhem"] = trades["mayhem"].astype(bool)
    trades, d, f = jocry_clean(trades)
    drops.update(d)
    fixes.update(f)
    trades["chain"] = trades["event_time"].astype("int64")
    trades["krank"] = KIND_RANK["trade"]
    trades["kind"] = "trade"
    toks = meta.tokens[meta.tokens["day"] == key].assign(kind="create", chain=lambda x: x["ms"],
                                                         krank=KIND_RANK["create"], id=-1)
    migs = meta.migrations[meta.migrations["day"] == key].assign(
        kind="migrate", chain=lambda x: x["ms"], krank=KIND_RANK["migrate"], id=-1)
    df = pd.concat([trades, toks, migs], ignore_index=True, sort=False)
    df.sort_values(["chain", "krank", "id"], inplace=True, kind="stable")
    t0, t1 = et_bounds(day)
    writer = DayWriter(tape_path(out_root if out_root is not None else DEV_ROOT, "jocry", day), lag_ms)
    for r in df.itertuples(index=False):
        chain = int(r.chain)
        ts = chain // 1000
        if r.kind == "trade":
            mm = bool(r.mayhem)
            writer.write(ChainEvent(
                "trade", "pump", signature=_s(r.tx_signature), index=0, ts=ts, mint=r.mint,
                user=_s(r.user_wallet), side="buy" if r.is_buy else "sell", quote=int(r.q),
                tokens=int(r.t), price=_price(r.vq, r.vb), reserve_quote=int(r.vq),
                reserve_base=int(r.vb), fee_bps=PUMP_FEE_BPS, progress=pump_progress(r.vb, mm),
                extra={"creator": _s(r.creator), "mayhem": mm}), chain)
        elif r.kind == "create":
            mm = bool(r.mayhem)
            vb = MAYHEM_V_TOKENS if mm else PUMP_V_TOKENS
            writer.write(ChainEvent(
                "create", "pump", "", 0, ts=ts, mint=r.mint, user=_s(r.creator),
                price=_price(PUMP_V_SOL, vb), reserve_quote=PUMP_V_SOL, reserve_base=vb,
                extra={"name": _s(r.name)[:64], "symbol": _s(r.symbol)[:32],
                       "creator": _s(r.creator), "bonding_curve": _s(r.bonding_curve_key),
                       "supply": 2_000_000_000 if mm else 1_000_000_000, "mayhem": mm}), chain)
        else:
            writer.write(ChainEvent("migrate", "pump", "", 0, ts=ts, mint=r.mint, progress=1.0), chain)
            pool = _s(r.pool_address)
            if pool and pool not in POOL_SENTINELS:
                writer.write(ChainEvent("pool", "pumpswap", "", 0, ts=ts, mint=r.mint, pool=pool,
                                        extra={"base_decimals": 6}), chain)
            else:
                drops["pool_row_sentinel_address"] += 1
    manifest = {"source": "jocry", "day": day.isoformat(), "split": "dev",
                "utc_window_ms": [t0, t1], "raw_rows": {"trade": raw, "create": len(toks),
                                                        "migrate": len(migs)},
                "dropped": {k: v for k, v in drops.items() if v}, "repaired": dict(fixes),
                "inputs": [p.name for p in parts],
                "chain_ms": "jocry event_time (websocket receive time), used as a proxy",
                "notes": ["fee 125 bps assumed (no fee field)",
                          "creates from tokens.detected_at; migrations from migrations.parquet",
                          "pool rows without reserves; sentinel pool addresses get no pool row",
                          "wallet BwWK17cb... (KNOWN_ISSUES: non-human, ~20% of trades) is kept: "
                          "it trades live too"]}
    return writer.close(manifest)


# ---------------------------------------------------------------- reading

def iter_day(path: Path):
    """Rows of one day tape, streamed (a whole Slinky21 day is too big to hold in memory,
    which tape.read_tape would do)."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def day_tapes(root: Path, source: str, start: date | None = None, end: date | None = None):
    """(day, path) of every converted day tape under root/source, oldest first."""
    for path in sorted((Path(root) / source).glob("*/day.jsonl.gz")):
        day = datetime.strptime(path.parent.name, "%Y%m%d").date()
        if (start and day < start) or (end and day > end):
            continue
        yield day, path


# ---------------------------------------------------------------- validation

def check_tape(path: Path) -> dict:
    """Replay a tape through Market only: rx order and, for every SOL-quoted pump trade,
    the relative gap between the market price after it and the row's own reserves."""
    from .market import Market
    from .replay import row_to_event
    market, last, bad_order, worst, n, next_prune = Market(), 0, 0, 0.0, 0, 0
    for row in iter_day(path):
        if row["rx"] >= next_prune:  # as live: forget coins idle for 30 minutes
            market.prune(row["rx"], set())
            next_prune = row["rx"] + 60_000
        if row["rx"] < last:
            bad_order += 1
        last = row["rx"]
        ev = row_to_event(row)
        st = market.apply(ev, row["rx"])
        if ev.kind == "trade" and st is not None and ev.quote_mint == WSOL and ev.reserve_base:
            want = _price(ev.reserve_quote, ev.reserve_base)
            err = abs(st.price - want) / want
            worst = max(worst, err)
            n += 1
    return {"rows_checked": n, "rx_out_of_order": bad_order, "max_rel_price_err": worst}


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="convert downloaded pump.fun history to tapes")
    ap.add_argument("--source", required=True, choices=["slinky21", "jocry"])
    ap.add_argument("--from", dest="start", default="")
    ap.add_argument("--to", dest="end", default="")
    ap.add_argument("--lag-ms", type=int, default=DEFAULT_LAG_MS)
    ap.add_argument("--out", default="", help="tape root (default: hist / hist_holdout by day)")
    ap.add_argument("--check", action="store_true", help="also validate each written tape")
    ap.add_argument("--force", action="store_true", help="rewrite days that already exist")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else None
    if args.source == "slinky21":
        index = SlinkyIndex()
        lo, hi = index.span_ms()
        first, last = et_day(lo), et_day(hi)
        meta = None
    else:
        meta = JocryMeta()
        first, last = et_day(int(meta.tokens["ms"].min())), et_day(int(meta.tokens["ms"].max()))
    a = date.fromisoformat(args.start) if args.start else first
    b = date.fromisoformat(args.end) if args.end else last
    days = list(daterange(max(a, first), min(b, last)))
    if args.source == "jocry":
        jocry_spill(days={int(d.strftime("%Y%m%d")) for d in days})
    state = {}
    for day in days:
        root = out if out is not None else root_of(split_of(args.source, day))
        path = tape_path(root, args.source, day)
        if path.exists() and not args.force:
            print(f"{day} exists, skipped", flush=True)
            continue
        t = time.time()
        if args.source == "slinky21":
            m = convert_slinky_day(day, index, root, args.lag_ms, state)
        else:
            m = convert_jocry_day(day, meta, out_root=root, lag_ms=args.lag_ms)
        line = {"day": m["day"], "split": m["split"], "rows": m["rows"], "kinds": m["rows_by_kind"],
                "dropped": m["dropped"], "secs": round(time.time() - t)}
        if args.check:
            line["check"] = check_tape(path)
            mpath = path.parent / "manifest.json"
            mj = json.loads(mpath.read_text(encoding="utf-8"))
            mj["check"] = line["check"]
            mpath.write_text(json.dumps(mj, indent=1), encoding="utf-8")
        print(json.dumps(line), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
