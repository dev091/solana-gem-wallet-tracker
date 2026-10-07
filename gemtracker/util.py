"""Small helpers: Solana address checks, number formatting, JSON files."""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDEX = {c: i for i, c in enumerate(B58_ALPHABET)}
ADDRESS_PATTERN = r"[1-9A-HJ-NP-Za-km-z]{32,44}"


def b58decode(text: str) -> bytes:
    num = 0
    for char in text:
        num = num * 58 + _B58_INDEX[char]  # KeyError on a non-base58 character
    body = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    leading_zeros = len(text) - len(text.lstrip("1"))
    return b"\0" * leading_zeros + body


def is_address(value) -> bool:
    """True for a valid Solana public key (base58 that decodes to 32 bytes)."""
    if not isinstance(value, str) or not 32 <= len(value) <= 44:
        return False
    try:
        return len(b58decode(value)) == 32
    except KeyError:
        return False


def to_seconds(value) -> int | None:
    """Unix time in seconds from seconds or milliseconds (APIs mix both)."""
    if value in (None, "", 0):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return int(num / 1000) if num > 1e11 else int(num)


def num(value, default: float = 0.0) -> float:
    try:
        return default if value is None else float(value)
    except (TypeError, ValueError):
        return default


def short(addr: str) -> str:
    return f"{addr[:4]}…{addr[-4:]}" if addr and len(addr) > 10 else (addr or "")


def usd(value) -> str:
    value = num(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1e6:
        return f"{sign}${value / 1e6:.2f}M"
    if value >= 1e4:
        return f"{sign}${value / 1e3:.1f}k"
    return f"{sign}${value:,.0f}"


def mult(value) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}x" if value >= 100 else f"{value:.1f}x"


def date(ts) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")


def now() -> int:
    return int(time.time())


def chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def load_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save_json(path: Path, obj, *, js_var: str | None = None) -> None:
    """Write JSON atomically. With js_var, also write <name>.js that sets window.<js_var>,
    so the dashboard works even when index.html is opened straight from disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=1, ensure_ascii=False)
    _atomic_write(path, text + "\n")
    if js_var:
        _atomic_write(path.with_suffix(".js"), f"window.{js_var} = {text};\n")


def _atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def read_wallet_list(path: Path) -> list:
    """Lines like `ADDRESS  optional label`; lines starting with '#' are comments.
    Returns [(address, label)]."""
    out = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if is_address(parts[0]):
            out.append((parts[0], parts[1].strip() if len(parts) > 1 else ""))
    return out
