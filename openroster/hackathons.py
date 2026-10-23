"""Hackathon site checker. For each entry in config/hackathons.yaml, crawl a few same-domain pages and find:
event dates (with evidence), application status, and links for volunteer / mentor / judge / organizer /
workshop-lead roles plus any deadline near them. Shallow and bounded: depth <= 2, <= `max_pages` pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlsplit

from pydantic import BaseModel, ConfigDict, Field
from selectolax.lexbor import LexborHTMLParser as HTMLParser

from .adapters.base import AdapterResult, Candidate, RoleCandidate
from .adapters.common import clean, parse_structured
from .adapters.jsonld import extract_events
from .config import Audit, latest_verdict, load_yaml
from .extract.classify import ROLE_RULES
from .extract.dates import find_deadline, parse_when
from .fetch import BudgetExceeded, Fetcher, FetchError, FetchRefused, policy_check

PRIORITY_LINK = re.compile(
    r"apply|register|faq|schedule|volunteer|mentor|judg|organi[sz]|team|join|workshop|speaker|sponsor|about|info",
    re.I,
)
ROLE_LINK = {
    "volunteer": re.compile(r"volunteer", re.I),
    "mentor": re.compile(r"\bmentor", re.I),
    "judge": re.compile(r"\bjudg", re.I),
    "organizer_team": re.compile(r"organi[sz]er|join (?:the|our) team|exec(?:utive)? team|we'?re hiring", re.I),
    "workshop_lead": re.compile(r"workshop (?:lead|host|proposal)|host a workshop|call for (?:speakers|workshops)", re.I),
}
APPS_OPEN = re.compile(r"\b(?:applications? (?:are )?(?:now )?open|apply now|registration (?:is )?(?:now )?open)\b", re.I)
APPS_CLOSED = re.compile(r"\b(?:applications? (?:are |have )?(?:now )?closed|registration (?:is |has )?(?:now )?closed)\b", re.I)
EVENT_CONTEXT = re.compile(r"\b(?:hackathon|takes? place|happening|join us|will be held|event dates?|when\b|this year)", re.I)


class Hackathon(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    url: str
    host: str | None = None                  # school id or organization
    city: str | None = None
    region: str | None = "CA-ON"
    country: str | None = "CA"
    mode: str | None = None
    reviewed: bool = False
    enabled: bool = True
    max_pages: int = 12
    infer_year: bool = False
    audit: Audit = Field(default_factory=Audit)


@dataclass
class Page:
    url: str
    text: str
    links: list[tuple[str, str]]   # (absolute url, link text)


def _page(url: str, html: str) -> Page:
    tree = HTMLParser(html)
    for bad in tree.css("script, style, noscript, svg"):
        if bad.attributes.get("type") != "application/ld+json":
            bad.decompose()
    body = tree.body or tree.root
    text = clean(body.text(separator=" ")) if body else ""
    links = []
    for a in tree.css("a[href]"):
        href = a.attributes.get("href") or ""
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        links.append((urldefrag(urljoin(url, href))[0], clean(a.text(separator=" "))))
    return Page(url, text, links)


def crawl(h: Hackathon, fetcher: Fetcher, source_id: str) -> tuple[list[Page], list[str], list[str]]:
    """BFS over the same host. Returns (pages, raw html list, errors)."""
    host = urlsplit(h.url).hostname
    fetcher.set_budget(source_id, h.max_pages)
    queue: list[tuple[str, int]] = [(h.url, 0)]
    seen: set[str] = set()
    pages: list[Page] = []
    raws: list[str] = []
    errors: list[str] = []
    while queue:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            r = fetcher.get(url, source_id=source_id)
        except BudgetExceeded:
            break
        except (FetchError, FetchRefused) as e:
            errors.append(str(e))
            continue
        if "html" not in r.content_type and r.content_type:
            continue
        p = _page(url, r.text)
        pages.append(p)
        raws.append(r.text)
        if depth >= 2:
            continue
        nxt = [(u, t) for u, t in p.links if urlsplit(u).hostname == host and u not in seen]
        nxt.sort(key=lambda ut: 0 if PRIORITY_LINK.search(ut[0] + " " + ut[1]) else 1)
        for u, t in nxt:
            if PRIORITY_LINK.search(u + " " + t):
                queue.append((u, depth + 1))
    return pages, raws, errors


def _event_dates(h: Hackathon, pages: list[Page], raws: list[str]) -> tuple[Candidate | None, str]:
    """JSON-LD first; otherwise the first date range on the home page in an event context."""
    for raw in raws:
        for ev in extract_events(raw):
            if ev.get("startDate"):
                start, all_day = parse_structured(ev.get("startDate"), "America/Toronto")
                end, _ = parse_structured(ev.get("endDate"), "America/Toronto")
                if start:
                    return Candidate(source_id=f"hackathon:{h.id}", adapter="hackathon_site", url=h.url,
                                     title=h.name, start=start, end=end, all_day=all_day,
                                     date_evidence=f"JSON-LD startDate {ev.get('startDate')}",
                                     date_confidence="structured"), ""
    for p in pages[:3]:
        for m in EVENT_CONTEXT.finditer(p.text):
            window = p.text[m.start() : m.start() + 160]
            d = parse_when(window, "America/Toronto", infer_year=h.infer_year)
            if d:
                return Candidate(source_id=f"hackathon:{h.id}", adapter="hackathon_site", url=h.url,
                                 title=h.name, start=d.start, end=d.end, all_day=d.all_day, timezone=d.timezone,
                                 date_evidence=d.evidence, date_confidence=d.confidence), ""
    evidence = next((p.text[:300] for p in pages if p.text), "")
    return None, evidence


def _roles(h: Hackathon, pages: list[Page]) -> list[RoleCandidate]:
    found: dict[str, RoleCandidate] = {}
    for p in pages:
        for url, text in p.links:
            label = f"{text} {url}"
            for role, rx in ROLE_LINK.items():
                if role in found or not rx.search(label):
                    continue
                # Deadline near the link text on the page that links to it.
                idx = p.text.find(text) if text else -1
                window = p.text[max(0, idx - 150) : idx + 300] if idx >= 0 else ""
                dl = find_deadline(window, "America/Toronto", infer_year=h.infer_year) if window else None
                # Role links (often to form hosts) are only linked, never fetched.
                found[role] = RoleCandidate(
                    role=role,
                    closes=dl.start if dl else None,
                    url=url,
                    evidence=(dl.evidence if dl else f"link: {text[:120]}")[:300],
                    status="open" if dl else "unknown",
                )
        # Calls stated in text without a dedicated link ("We're looking for mentors! Apply by Jan 5")
        for role, rx in ROLE_RULES:
            if role in found:
                continue
            m = rx.search(p.text)
            if m and re.search(r"\b(?:apply|sign up|applications?|looking for|wanted|calling)\b",
                               p.text[max(0, m.start() - 80) : m.end() + 80], re.I):
                window = p.text[max(0, m.start() - 80) : m.end() + 200]
                dl = find_deadline(window, "America/Toronto", infer_year=h.infer_year)
                found[role] = RoleCandidate(role=role, closes=dl.start if dl else None, url=p.url,
                                            evidence=(dl.evidence if dl else window)[:300],
                                            status="open" if dl else "unknown")
    return list(found.values())


def check(h: Hackathon, fetcher: Fetcher) -> tuple[Candidate, int, list[str]]:
    sid = f"hackathon:{h.id}"
    pages, raws, errors = crawl(h, fetcher, sid)
    if not pages:
        c = Candidate(source_id=sid, adapter="hackathon_site", url=h.url, title=h.name,
                      review_reasons=["site could not be fetched: " + "; ".join(errors)[:150]])
        return c, 0, errors
    cand, evidence = _event_dates(h, pages, raws)
    all_text = " ".join(p.text for p in pages)
    if cand is None:
        cand = Candidate(source_id=sid, adapter="hackathon_site", url=h.url, title=h.name,
                         date_evidence=evidence, date_confidence="none",
                         review_reasons=["no event date found with confidence (site may be JS-only or not updated)"])
    participant = RoleCandidate(role="participant", url=h.url)
    if APPS_CLOSED.search(all_text):
        participant.status = "closed"
    elif APPS_OPEN.search(all_text):
        participant.status = "open"
    dl = find_deadline(all_text, "America/Toronto", infer_year=h.infer_year)
    if dl and cand.start and dl.start <= cand.start:
        participant.closes, participant.evidence = dl.start, dl.evidence
    cand.roles = [participant, *_roles(h, pages)]
    cand.type = "hackathon"
    cand.uid = f"hackathon:{h.id}"
    cand.organizer = h.name
    cand.city, cand.region, cand.country, cand.mode = h.city, h.region, h.country, h.mode
    cand.schools = None
    cand.text = all_text[:4000]
    return cand, len(pages), errors


def load_hackathons() -> list[Hackathon]:
    return [Hackathon(**h) for h in (load_yaml("hackathons.yaml").get("hackathons") or [])]


def check_all(fetcher: Fetcher, only: set[str] | None = None) -> tuple[AdapterResult, dict]:
    from .pipeline.run import SourceHealth

    res = AdapterResult()
    health: dict[str, SourceHealth] = {}
    for h in load_hackathons():
        if only and h.id not in only:
            continue
        if not (h.enabled and h.reviewed and latest_verdict(f"hackathon:{h.id}", h.audit.verdict) == "allowed"):
            continue
        try:
            policy_check(h.url)
        except FetchRefused as e:
            health[f"hackathon:{h.id}"] = SourceHealth(False, 0, 0, 0, str(e), refused=True)
            continue
        cand, pages, errors = check(h, fetcher)
        res.candidates.append(cand)
        res.pages += pages
        ok = pages > 0
        health[f"hackathon:{h.id}"] = SourceHealth(ok, 1 if cand.start else 0, 1, pages,
                                                    "; ".join(errors)[:300] or None)
    return res, health
