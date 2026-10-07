"""Small HTTP client on the standard library, so nothing has to be pip-installed.

Every call retries with backoff on rate limits / server errors, and hosts can be
paced (max N requests per second) so free API tiers are not hammered.
"""
from __future__ import annotations

import gzip
import http.client
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504, 520, 522, 524}
_SECRET_QUERY = re.compile(r"((?:api[-_]?key|apikey|key|token)=)[^&\s]+", re.I)
_SECRET_PATH = re.compile(r"(/bot)[^/\s]+")  # Telegram bot token lives in the path


class HttpError(Exception):
    def __init__(self, status: int, url: str, body: str = ""):
        self.status = status
        self.url = redact(url)
        self.body = body
        snippet = " ".join(body.split())[:160]
        where = f"HTTP {status}" if status else "request failed"
        super().__init__(f"{where} for {self.url}" + (f": {snippet}" if snippet else ""))


def redact(url: str) -> str:
    """Hide API keys before a URL is printed or stored."""
    return _SECRET_PATH.sub(r"\1***", _SECRET_QUERY.sub(r"\1***", url))


class _Pacer:
    def __init__(self, rps: float):
        self.interval = 1.0 / rps
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            start = max(now, self.next_at)
            self.next_at = start + self.interval
        if start > now:
            time.sleep(start - now)


_pacers: dict = {}


def set_rate(host: str, rps: float) -> None:
    """Allow at most `rps` requests per second to `host`, shared by all threads."""
    if host and rps and rps > 0:
        _pacers[host] = _Pacer(rps)


def _retry_delay(exc: urllib.error.HTTPError, attempt: int) -> float:
    after = exc.headers.get("Retry-After") if exc.headers else None
    if after and after.strip().isdigit():
        return min(float(after), 60.0)
    return min(1.5 * 2 ** attempt, 30.0)


def _error_body(exc: urllib.error.HTTPError) -> str:
    try:
        raw = exc.read()
        if exc.headers and exc.headers.get("Content-Encoding", "").lower() == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "replace")
    except Exception:
        return ""


def request(method: str, url: str, *, params: dict | None = None, headers: dict | None = None,
            json_body=None, timeout: float = 45.0, retries: int = 4, as_json: bool = True):
    if params:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        url = f"{url}{'&' if '?' in url else '?'}{query}"
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            "Accept-Encoding": "gzip"}
    if headers:
        hdrs.update(headers)
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    pacer = _pacers.get(urllib.parse.urlsplit(url).hostname or "")

    for attempt in range(retries + 1):
        if pacer:
            pacer.wait()
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
        except urllib.error.HTTPError as exc:
            if exc.code in RETRY_STATUS and attempt < retries:
                time.sleep(_retry_delay(exc, attempt))
                continue
            raise HttpError(exc.code, url, _error_body(exc)) from None
        except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
            reason = str(getattr(exc, "reason", exc))
            if "Tunnel connection failed" in reason:  # a proxy refused this host: retrying won't help
                raise HttpError(0, url, f"blocked by network proxy ({reason})") from None
            if attempt < retries:
                time.sleep(min(2 ** attempt, 15))
                continue
            raise HttpError(0, url, f"network error: {reason}") from None

        text = raw.decode("utf-8", "replace")
        if not as_json:
            return text
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except ValueError:
            raise HttpError(200, url, "response is not JSON: " + text[:120]) from None
    raise AssertionError("unreachable")


def get_json(url: str, **kw):
    return request("GET", url, **kw)


def post_json(url: str, body, **kw):
    return request("POST", url, json_body=body, **kw)


def get_text(url: str, **kw) -> str:
    return request("GET", url, as_json=False, **kw)
