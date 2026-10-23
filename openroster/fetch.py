"""The polite fetcher. Every network request in OpenRoster goes through `Fetcher`.

Rules enforced here (see PLAN.md §4):
- honest User-Agent with the repo URL and contact address
- known verdicts: blocked / link-only / permission-required hosts are refused in code
- robots.txt is obeyed for every URL, including each redirect hop
- at most one request every `min_interval` seconds per host, never in parallel
- conditional requests (ETag / Last-Modified) with an on-disk cache
- backoff on 429/5xx, honouring Retry-After
- a per-source page budget
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
from protego import Protego

from .config import DATA, known_verdict_for, user_agent

MAX_REDIRECTS = 5
MAX_BYTES = 5_000_000


class FetchRefused(Exception):
    """The request is not allowed by policy (known verdict or robots.txt)."""


class BudgetExceeded(Exception):
    pass


class FetchError(Exception):
    def __init__(self, url: str, status: int | None, msg: str):
        super().__init__(f"{url}: {msg}")
        self.url = url
        self.status = status


@dataclass
class Response:
    url: str
    status: int
    text: str
    headers: dict[str, str]
    from_cache: bool = False

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "").split(";")[0].strip().lower()


def policy_check(url: str) -> None:
    """Raise FetchRefused if a known verdict forbids fetching this URL."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise FetchRefused(f"{url}: only http(s) is fetched")
    kv = known_verdict_for(url)
    if kv is None:
        return
    path_ok = kv.allow_paths is None or any(parts.path.startswith(p) for p in kv.allow_paths)
    if kv.verdict == "allowed" and path_ok:
        return
    if kv.verdict == "permission_required" and kv.permission and kv.permission.get("granted"):
        return
    raise FetchRefused(f"{url}: {kv.verdict} ({kv.reason})")


@dataclass
class Fetcher:
    min_interval: float = 2.0
    cache_dir: Path = field(default_factory=lambda: DATA / "cache")
    transport: httpx.BaseTransport | None = None
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    max_retries: int = 3
    respect_robots: bool = True

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": user_agent(), "Accept-Language": "en-CA,en;q=0.8"},
            timeout=httpx.Timeout(20.0),
            follow_redirects=False,
            transport=self.transport,
        )
        self._last: dict[str, float] = {}
        self._robots: dict[str, Protego | None] = {}
        self._budget: dict[str, int] = {}
        self.requests_made = 0

    # ---- budget -------------------------------------------------------------------------------------
    def set_budget(self, source_id: str, pages: int) -> None:
        self._budget[source_id] = pages

    def _spend(self, source_id: str | None) -> None:
        if source_id is None:
            return
        left = self._budget.get(source_id)
        if left is None:
            return
        if left <= 0:
            raise BudgetExceeded(f"page budget exhausted for {source_id}")
        self._budget[source_id] = left - 1

    # ---- rate limiting ------------------------------------------------------------------------------
    def interval_for(self, host: str) -> float:
        """At least `min_interval`, or the site's robots.txt Crawl-delay if that is longer (capped at 120 s)."""
        delays = [
            rp.crawl_delay("OpenRosterBot") or 0
            for origin, rp in self._robots.items()
            if rp is not None and urlsplit(origin).netloc == host
        ]
        return max([self.min_interval, *(min(float(d), 120.0) for d in delays)])

    def _wait_turn(self, host: str) -> None:
        last = self._last.get(host)
        if last is not None:
            wait = self.interval_for(host) - (self.clock() - last)
            if wait > 0:
                self.sleep(wait)
        self._last[host] = self.clock()

    # ---- robots -------------------------------------------------------------------------------------
    def robots_for(self, url: str) -> Protego | None:
        """Parsed robots.txt for the URL's origin; None means 'no restrictions' (404 etc.)."""
        p = urlsplit(url)
        origin = f"{p.scheme}://{p.netloc}"
        if origin in self._robots:
            return self._robots[origin]
        robots_url = origin + "/robots.txt"
        self._wait_turn(p.netloc)
        self.requests_made += 1
        try:
            r = self._client.get(robots_url, follow_redirects=True)
        except httpx.HTTPError:
            # RFC 9309: unreachable robots.txt means assume complete disallow.
            parsed: Protego | None = Protego.parse("User-agent: *\nDisallow: /")
        else:
            if r.status_code >= 500:
                parsed = Protego.parse("User-agent: *\nDisallow: /")
            elif r.status_code >= 400:
                parsed = None
            else:
                parsed = Protego.parse(r.text)
        self._robots[origin] = parsed
        return parsed

    def robots_allows(self, url: str) -> bool:
        rp = self.robots_for(url)
        return True if rp is None else rp.can_fetch(url, "OpenRosterBot")

    # ---- cache --------------------------------------------------------------------------------------
    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha256(url.encode()).hexdigest()[:32] + ".json")

    def _cache_get(self, url: str) -> dict | None:
        p = self._cache_path(url)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except (OSError, json.JSONDecodeError):
                return None
        return None

    def _cache_put(self, url: str, resp: httpx.Response, text: str) -> None:
        validators = {k: resp.headers[k] for k in ("etag", "last-modified") if k in resp.headers}
        if not validators:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {"url": url, "validators": validators, "text": text, "headers": dict(resp.headers)}
        self._cache_path(url).write_text(json.dumps(payload))

    # ---- main entry ---------------------------------------------------------------------------------
    def get(self, url: str, source_id: str | None = None, accept: str | None = None) -> Response:
        hops = 0
        current = url
        while True:
            policy_check(current)
            if self.respect_robots and not self.robots_allows(current):
                raise FetchRefused(f"{current}: disallowed by robots.txt")
            resp = self._get_once(current, source_id, accept)
            if resp.status in (301, 302, 303, 307, 308):
                hops += 1
                if hops > MAX_REDIRECTS:
                    raise FetchError(url, resp.status, "too many redirects")
                current = urljoin(current, resp.headers.get("location", ""))
                continue
            return resp

    def _get_once(self, url: str, source_id: str | None, accept: str | None) -> Response:
        cached = self._cache_get(url)
        headers: dict[str, str] = {}
        if accept:
            headers["Accept"] = accept
        if cached:
            v = cached["validators"]
            if "etag" in v:
                headers["If-None-Match"] = v["etag"]
            if "last-modified" in v:
                headers["If-Modified-Since"] = v["last-modified"]
        host = urlsplit(url).netloc
        attempt = 0
        while True:
            self._spend(source_id)
            self._wait_turn(host)
            self.requests_made += 1
            try:
                r = self._client.get(url, headers=headers)
            except httpx.HTTPError as e:
                if attempt >= self.max_retries:
                    raise FetchError(url, None, f"network error: {e}") from e
                attempt += 1
                self.sleep(min(60.0, 2.0 * 2**attempt))
                continue
            if r.status_code == 304 and cached:
                return Response(url, 200, cached["text"], cached.get("headers", {}), from_cache=True)
            if r.status_code in (429, 500, 502, 503, 504):
                if attempt >= self.max_retries:
                    raise FetchError(url, r.status_code, "server kept failing")
                attempt += 1
                retry_after = r.headers.get("retry-after", "")
                delay = float(retry_after) if retry_after.isdigit() else 2.0 * 2**attempt
                self.sleep(min(300.0, delay))
                continue
            if r.status_code in (301, 302, 303, 307, 308):
                return Response(url, r.status_code, "", dict(r.headers))
            if r.status_code >= 400:
                raise FetchError(url, r.status_code, f"HTTP {r.status_code}")
            if len(r.content) > MAX_BYTES:
                raise FetchError(url, r.status_code, "response too large")
            text = r.text
            self._cache_put(url, r, text)
            return Response(url, r.status_code, text, {k.lower(): v for k, v in r.headers.items()})

    def close(self) -> None:
        self._client.close()
