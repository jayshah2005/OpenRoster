"""Source audit: robots.txt, terms of use, platform detection, verdict.

The verdict is provisional. A keyword scan cannot read terms with legal accuracy, so every source also needs
the owner's `reviewed: true` before it runs.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from urllib.parse import quote, unquote, urljoin, urlsplit

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from ..adapters.common import clean
from ..adapters.jsonld import extract_events
from ..config import known_verdict_for
from ..extract.dates import MDY
from ..fetch import Fetcher, FetchError, FetchRefused, policy_check

TERMS_LINK = re.compile(r"terms|legal|conditions|terms-of-use|terms-of-service|tos\b|disclaimer|copyright", re.I)
AUTOMATED = re.compile(
    r"scrap(?:e|ing|er)|crawl(?:er|ing)?|spider|robots?\b|bots?\b|automated (?:means|access|system|query|queries|tools?)"
    r"|data[- ]mining|harvest(?:ing)?|extract(?:ion)? (?:of )?(?:data|content)",
    re.I,
)
REPUBLISH = re.compile(r"republish|re-publish|reproduc|redistribut|commercial (?:use|purpose)|personal(?:,)? non-commercial", re.I)
FORBID = re.compile(
    r"\b(?:not|prohibit\w*|forbid\w*|may not|must not|shall not|no\b|without (?:our |the )?(?:prior |express )?(?:written )?(?:consent|permission))",
    re.I,
)
SENTENCE = re.compile(r"[^.!?]{0,400}[.!?]")
GCAL_EMBED = re.compile(r"calendar\.google\.com/calendar/(?:u/\d+/)?embed\?[^\"'\s>]*?src=([^&\"'\s>]+)", re.I)
LUMA_ICS = re.compile(r"https://api\.lu\.ma/ics/get\?entity=calendar&(?:amp;)?id=cal-[A-Za-z0-9]+")
LOGIN = re.compile(r"\b(?:sign in|log in|login|single sign-on|sso)\b", re.I)


@dataclass
class AuditResult:
    url: str
    checked: str
    verdict: str = "unknown"
    reasons: list[str] = field(default_factory=list)
    known_verdict: str | None = None
    robots: str = "unknown"            # allowed | disallowed | no_robots | unreachable | not_checked
    sitemaps: list[str] = field(default_factory=list)
    terms_url: str | None = None
    terms_forbid_automated: bool | None = None
    terms_forbid_republish: bool | None = None
    terms_quotes: list[str] = field(default_factory=list)
    platform: str = "unknown"
    feeds: list[str] = field(default_factory=list)
    jsonld_events: int = 0
    dated_items_in_html: int = 0
    login_wall: bool = False
    http_status: int | None = None

    def to_audit(self) -> dict:
        return {
            "robots": self.robots,
            "terms_url": self.terms_url,
            "terms_forbid": bool(self.terms_forbid_automated or self.terms_forbid_republish),
            "verdict": self.verdict,
            "checked": self.checked[:10],
            "notes": "; ".join(self.reasons)[:500],
        }


def _sentences(text: str, rx: re.Pattern[str]) -> list[str]:
    out = []
    for m in SENTENCE.finditer(text):
        s = m.group(0).strip()
        if rx.search(s):
            out.append(re.sub(r"\s+", " ", s)[:240])
    return out


def scan_terms(text: str) -> tuple[bool, bool, list[str]]:
    auto = [s for s in _sentences(text, AUTOMATED) if FORBID.search(s)]
    repub = [s for s in _sentences(text, REPUBLISH) if FORBID.search(s) or "non-commercial" in s.lower()]
    return bool(auto), bool(repub), (auto[:2] + repub[:2])


def gen_hint(html: str) -> str:
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    return m.group(1) if m else ""


def detect_platform(url: str, html: str, fetcher: Fetcher, res: AuditResult) -> None:
    tree = HTMLParser(html)
    p = urlsplit(url)
    origin = f"{p.scheme}://{p.netloc}"
    # Feeds advertised on the page.
    for a in tree.css("a[href], link[href]"):
        href = a.attributes.get("href") or ""
        if re.search(r"\.ics\b|webcal:|/ical\b|ical=|outlook-ical|format=ical", href, re.I):
            res.feeds.append(urljoin(url, href.replace("webcal://", "https://")))
    for m in GCAL_EMBED.finditer(html):
        cal_id = unquote(m.group(1))
        res.feeds.append(f"https://calendar.google.com/calendar/ical/{quote(cal_id, safe='')}/public/basic.ics")
    res.feeds.extend(LUMA_ICS.findall(html))
    # Campus Labs Engage (used by Brock, Sheridan and others) publishes every public event as RSS.
    if "campuslabs" in html.lower() or "engage" in gen_hint(html).lower():
        prefix = "/engage" if p.path.startswith("/engage") else ""
        res.feeds.append(f"{origin}{prefix}/events.rss")
    res.feeds = list(dict.fromkeys(res.feeds))[:10]
    res.jsonld_events = len(extract_events(html))
    body_text = clean(tree.body.text(separator=" ")) if tree.body else ""
    res.dated_items_in_html = len(MDY.findall(body_text))
    gen_meta = tree.css_first('meta[name="generator"]')
    gen = (gen_meta.attributes.get("content") or "") if gen_meta is not None else ""

    def probe(path: str, key: str) -> bool:
        try:
            r = fetcher.get(origin + path, accept="application/json")
            return r.status == 200 and key in json.loads(r.text)
        except (FetchError, FetchRefused, ValueError):
            return False

    looks_tribe = "tribe-events" in html or "/wp-json/tribe/" in html or ("WordPress" in gen and "events" in url)
    if looks_tribe and probe("/wp-json/tribe/events/v1/events?per_page=1", "events"):
        res.platform = "tribe"
        return
    if "localist" in html.lower() and probe("/api/2/events?pp=1", "events"):
        res.platform = "localist"
        return
    if res.feeds:
        res.platform = "ics"
    elif res.jsonld_events:
        res.platform = "jsonld"
    elif res.dated_items_in_html >= 2:
        res.platform = "html"
    elif len(body_text) < 400 and len(tree.css("script")) > 3:
        res.platform = "js_only"
    else:
        res.platform = "html_no_dates"


def audit_url(url: str, fetcher: Fetcher | None = None) -> AuditResult:
    fetcher = fetcher or Fetcher()
    res = AuditResult(url=url, checked=datetime.now(UTC).isoformat())
    kv = known_verdict_for(url)
    if kv:
        res.known_verdict = kv.verdict
        res.reasons.append(f"known verdict: {kv.reason}")
    try:
        policy_check(url)
    except FetchRefused:
        res.verdict = "permission_required" if kv and kv.verdict == "permission_required" else "blocked"
        if kv and kv.verdict == "link_only":
            res.reasons.append("link-only host: never fetched or submitted")
        res.robots = "not_checked"
        return res

    rp = fetcher.robots_for(url)
    if rp is None:
        res.robots = "no_robots"
    else:
        res.sitemaps = list(rp.sitemaps)
        res.robots = "allowed" if rp.can_fetch(url, "OpenRosterBot") else "disallowed"
    if res.robots == "disallowed":
        res.verdict = "blocked"
        res.reasons.append("robots.txt disallows this path for our user agent")
        return res

    try:
        page = fetcher.get(url)
        res.http_status = page.status
    except FetchError as e:
        res.http_status = e.status
        if e.status in (401, 403):
            res.login_wall = True
            res.verdict = "blocked"
            res.reasons.append(f"HTTP {e.status}: login wall or bot protection; not bypassed")
        else:
            res.verdict = "unknown"
            res.reasons.append(f"page could not be fetched: {e}")
        return res
    except FetchRefused as e:
        # Typically a redirect to another site that blocks us, or a blocked host.
        res.verdict = "blocked"
        res.reasons.append(f"refused: {e}")
        return res
    html = page.text
    tree = HTMLParser(html)

    # Terms of use
    for a in tree.css("a[href]"):
        label = f"{a.text(strip=True)} {a.attributes.get('href', '')}"
        if TERMS_LINK.search(label):
            res.terms_url = urljoin(url, a.attributes.get("href") or "")
            break
    if res.terms_url:
        try:
            t = fetcher.get(res.terms_url)
            body = HTMLParser(t.text).body
            auto, repub, quotes = scan_terms(clean(body.text(separator=" ")) if body else "")
            res.terms_forbid_automated, res.terms_forbid_republish, res.terms_quotes = auto, repub, quotes
        except (FetchError, FetchRefused) as e:
            res.reasons.append(f"terms page not readable: {e}")
    else:
        res.reasons.append("no terms-of-use link found on the page")

    detect_platform(url, html, fetcher, res)
    if tree.css_first('input[type="password"]') and res.dated_items_in_html == 0 and not res.feeds:
        res.login_wall = True

    if kv and kv.verdict != "allowed":
        res.verdict = kv.verdict
    elif res.login_wall:
        res.verdict = "blocked"
        res.reasons.append("page requires login")
    elif res.terms_forbid_automated:
        res.verdict = "blocked"
        res.reasons.append("terms appear to forbid automated access (owner should read the quotes)")
    elif res.platform == "js_only":
        res.verdict = "allowed"
        res.reasons.append("JS-only page: needs the headless adapter or a feed")
    else:
        res.verdict = "allowed"
    if res.terms_forbid_republish:
        res.reasons.append("terms restrict republishing: store facts only, link to the original (already our policy)")
    return res


def format_result(r: AuditResult) -> str:
    lines = [
        f"URL:        {r.url}",
        f"Verdict:    {r.verdict.upper()}",
        f"Robots:     {r.robots}",
        f"Terms:      {r.terms_url or '-'}",
        f"  forbids automated access: {r.terms_forbid_automated}",
        f"  restricts republishing:   {r.terms_forbid_republish}",
    ]
    lines += [f'  > "{q}"' for q in r.terms_quotes]
    lines += [
        f"Platform:   {r.platform}",
        f"Feeds:      {', '.join(r.feeds) or '-'}",
        f"JSON-LD events: {r.jsonld_events}   dated items in HTML: {r.dated_items_in_html}",
    ]
    if r.known_verdict:
        lines.append(f"Known verdict: {r.known_verdict}")
    lines += [f"Reason:     {x}" for x in r.reasons]
    return "\n".join(lines)


def result_dict(r: AuditResult) -> dict:
    return asdict(r)
