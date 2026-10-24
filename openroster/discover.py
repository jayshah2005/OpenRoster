"""Rule-based discovery of new sources. Runs weekly and makes no network requests of its own.

It reuses what the pipeline already knows:
- calendar feeds (iCal links, Google Calendar embeds, official Luma iCal links) that the audit found on pages of
  allowed sources, and
- hackathons that appear in the data (Hack Club, submissions, other feeds) with an official website that is not
  in config/hackathons.yaml yet.

Everything it proposes starts as `reviewed: false`, so nothing is fetched until the owner signs off through the
usual audit and Source review PR.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import yaml

from .audit.report import load_results
from .config import CONFIG, ROOT, known_verdict_for, load_sources, load_yaml
from .pipeline import store

DISCOVERED_SOURCES = CONFIG / "sources" / "discovered.yaml"
REPORT = ROOT / "reports" / "discovery.md"


@dataclass
class Discovery:
    sources: list[dict] = field(default_factory=list)
    hackathons: list[dict] = field(default_factory=list)


def _norm(url: str) -> str:
    p = urlsplit(url)
    return f"{(p.hostname or '').removeprefix('www.')}{p.path.rstrip('/')}".lower()


def _slug(s: str, n: int = 50) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-")


def _usable(url: str) -> bool:
    """Only URLs we could ever fetch: not blocked, not permission-required, not a form host."""
    kv = known_verdict_for(url)
    if kv is None:
        return True
    if kv.verdict != "allowed":
        return False
    return kv.allow_paths is None or any(urlsplit(url).path.startswith(p) for p in kv.allow_paths)


def discover() -> Discovery:
    found = Discovery()
    known_urls = {_norm(s.url) for s in load_sources()}
    hackathons = load_yaml("hackathons.yaml").get("hackathons") or []
    known_hosts = {(urlsplit(h["url"]).hostname or "").removeprefix("www.") for h in hackathons}
    by_id = {s.id: s for s in load_sources()}

    # 1. Feeds advertised on audited, allowed pages.
    for sid, audit in sorted(load_results().items()):
        if audit.get("verdict") != "allowed":
            continue
        parent = by_id.get(sid)
        for feed in audit.get("feeds") or []:
            if _norm(feed) in known_urls or not _usable(feed):
                continue
            known_urls.add(_norm(feed))
            found.sources.append({
                "id": f"{sid}-feed-{len([s for s in found.sources if s['id'].startswith(sid)]) + 1}",
                "name": f"Calendar feed found on {parent.name if parent else sid}",
                "adapter": "rss" if re.search(r"\.rss\b|/rss\b|feed=rss|\.xml\b", feed) else "ics",
                "url": feed,
                "owner": parent.owner if parent else sid.split(":")[-1],
                "enabled": True,
                "reviewed": False,
                "page_budget": 2,
                "schools": parent.schools if parent else [],
                "options": {"filter": "cs", "landing_url": audit.get("url")},
                "notes": f"Discovered by `openroster discover` on {audit.get('url')}",
            })

    # 2. Hackathons in the data whose official site we don't check yet (Canada only, to stay on focus).
    for rec in store.load_records().values():
        if rec.type != "hackathon" or rec.location.country not in ("CA", None):
            continue
        url = rec.registration.url or rec.sources[0].url
        host = (urlsplit(url).hostname or "").removeprefix("www.")
        if not host or host in known_hosts or not _usable(url):
            continue
        known_hosts.add(host)
        found.hackathons.append({
            "id": _slug(rec.title),
            "name": rec.title,
            "url": url,
            "host": None,
            "city": rec.location.city,
            "region": rec.location.region,
            "country": rec.location.country or "CA",
            "reviewed": False,
            "enabled": True,
            "notes": f"Discovered from listing {rec.id} ({', '.join(rec.obtained_via)})",
        })
    return found


def write(found: Discovery) -> dict[str, int]:
    """Append discoveries to config (never touching existing entries) and write a short report."""
    existing = (yaml.safe_load(DISCOVERED_SOURCES.read_text()) or {}).get("sources", []) if DISCOVERED_SOURCES.exists() else []
    ids = {s["id"] for s in existing}
    new_sources = [s for s in found.sources if s["id"] not in ids]
    if new_sources:
        DISCOVERED_SOURCES.write_text(
            "# Sources found by `openroster discover` and the weekly discovery agent. All start unreviewed:\n"
            "# the audit runs on them and the owner signs off in the Source review PR before anything is fetched.\n"
            + yaml.safe_dump({"sources": existing + new_sources}, sort_keys=False, allow_unicode=True, width=110)
        )
    path = CONFIG / "hackathons.yaml"
    doc = yaml.safe_load(path.read_text()) or {}
    have = {h["id"] for h in doc.get("hackathons") or []}
    new_hacks = [h for h in found.hackathons if h["id"] not in have]
    if new_hacks:
        doc["hackathons"] = sorted((doc.get("hackathons") or []) + new_hacks, key=lambda h: h["name"].lower())
        header = "".join(line for line in path.read_text().splitlines(keepends=True) if line.startswith("#"))
        path.write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110))
    lines = ["# Weekly discovery", "", f"New calendar feeds: **{len(new_sources)}** · new hackathon sites: **{len(new_hacks)}**", ""]
    lines += [f"- feed `{s['id']}`: {s['url']}" for s in new_sources]
    lines += [f"- hackathon `{h['id']}`: [{h['name']}]({h['url']})" for h in new_hacks]
    lines += ["", "All entries start with `reviewed: false`; the audit and the Source review PR decide whether they run.", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    return {"sources": len(new_sources), "hackathons": len(new_hacks)}
