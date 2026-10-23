"""Turn research/*.yaml (agent output) into config/sources/*.yaml, config/schools.yaml and config/hackathons.yaml.

Every generated source has `reviewed: false`; the owner signs off by merging the source-review PR.
Existing hand-tuned entries (same id) in config/ are kept as they are.

Usage: uv run python scripts/research_to_config.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"
CONFIG = ROOT / "config"

ADAPTER = {"tribe": "tribe", "localist": "localist", "ics": "ics", "jsonld": "jsonld", "sitemap": "sitemap",
           "html": "html", "js_only": "headless"}
BLOCKED_HOSTS = re.compile(r"(^|\.)(devpost\.com|mlh\.io|mlh\.com|eventbrite\.\w+|linkedin\.com|joinhandshake\.com)$")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def host(url: str) -> str:
    return re.sub(r"^https?://([^/]+).*$", r"\1", url or "").lower()


def source_entry(s: dict, group: str) -> dict | None:
    url = s.get("url") or ""
    platform = s.get("platform")
    if not url or BLOCKED_HOSTS.search(host(url)) or s.get("login_required") or s.get("blocked_by"):
        return None
    adapter = "hackclub" if platform == "api" and "hackclub" in url else ADAPTER.get(platform or "")
    if adapter is None:
        return None
    needs_selectors = adapter in ("html", "headless")
    relevance = s.get("cs_relevance", "medium")
    entry = {
        "id": s["id"],
        "name": s.get("name", s["id"]),
        "adapter": adapter,
        "url": url,
        "owner": s.get("owner") or group,
        "enabled": not needs_selectors,
        "reviewed": False,
        "page_budget": 10 if adapter in ("tribe", "localist", "sitemap") else 3,
        "options": {"filter": "all" if relevance == "high" else "cs"},
    }
    if s.get("landing_url") and s["landing_url"] != url:
        entry["options"]["landing_url"] = s["landing_url"]
    if s.get("expected_types") and len(s["expected_types"]) == 1:
        entry["default_type"] = s["expected_types"][0]
    owner = s.get("owner")
    if owner and group.startswith("schools"):
        entry["schools"] = [owner] if s.get("school_only") else []
    note = s.get("notes") or ""
    if needs_selectors:
        note = ("NEEDS SELECTORS before enabling. " + note).strip()
    if note:
        entry["notes"] = note[:400]
    return entry


def main() -> int:
    files = sorted(RESEARCH.glob("*.yaml"))
    if not files:
        print("no research files", file=sys.stderr)
        return 1
    (CONFIG / "sources").mkdir(parents=True, exist_ok=True)
    schools: dict[str, dict] = {}
    hackathons: dict[str, dict] = {}
    existing_h = {h["id"]: h for h in (load(CONFIG / "hackathons.yaml").get("hackathons") or [])} \
        if (CONFIG / "hackathons.yaml").exists() else {}

    for f in files:
        doc = load(f)
        group = doc.get("agent") or f.stem
        out_path = CONFIG / "sources" / f"{f.stem}.yaml"
        kept = {s["id"]: s for s in (load(out_path).get("sources") or [])} if out_path.exists() else {}
        entries = []
        for s in doc.get("sources") or []:
            if not s.get("id"):
                continue
            if s["id"] in kept and kept[s["id"]].get("hand_tuned"):
                entries.append(kept[s["id"]])
                continue
            e = source_entry(s, group)
            if e:
                if s["id"] in kept:  # keep owner decisions
                    for k in ("reviewed", "enabled", "options", "page_budget", "default_type", "default_roles"):
                        if k in kept[s["id"]]:
                            e[k] = kept[s["id"]][k]
                entries.append(e)
        for cal in doc.get("luma_calendars") or []:
            if not cal.get("ical_url"):
                continue
            sid = "luma-" + slug(cal["name"])
            e = kept.get(sid) or {
                "id": sid, "name": f"{cal['name']} (Luma iCal)", "adapter": "ics", "url": cal["ical_url"],
                "owner": slug(cal["name"]), "enabled": True, "reviewed": False, "page_budget": 2,
                "options": {"filter": "all" if cal.get("student_focus") else "cs",
                            "landing_url": cal.get("landing_url")},
                "notes": f"City: {cal.get('city')}",
            }
            entries.append(e)
        hand = [s for s in kept.values() if s.get("hand_tuned") and s["id"] not in {e["id"] for e in entries}]
        entries.extend(hand)
        if entries:
            out_path.write_text(
                f"# Generated from research/{f.name} by scripts/research_to_config.py.\n"
                "# Entries with `hand_tuned: true` are never overwritten.\n"
                + yaml.safe_dump({"sources": entries}, sort_keys=False, allow_unicode=True, width=110)
            )
            print(f"{out_path.relative_to(ROOT)}: {len(entries)} sources")

        for sc in doc.get("schools") or []:
            schools[sc["id"]] = {
                "id": sc["id"], "name": sc["name"], "kind": sc.get("kind"), "website": sc.get("website"),
                "aliases": sc.get("aliases", []), "campuses": sc.get("campuses", []),
            }
            for hk in sc.get("hackathons") or []:
                add_hackathon(hackathons, existing_h, hk, host_school=sc["id"])
        for hk in doc.get("hackathons") or []:
            add_hackathon(hackathons, existing_h, hk)

    if schools:
        prev = load(CONFIG / "schools.yaml").get("schools", []) if (CONFIG / "schools.yaml").exists() else []
        for p in prev:
            schools.setdefault(p["id"], p)
        (CONFIG / "schools.yaml").write_text(
            "# Schools and campus coordinates (used for 'near school' filters).\n"
            + yaml.safe_dump({"schools": sorted(schools.values(), key=lambda s: s["name"])},
                             sort_keys=False, allow_unicode=True, width=110)
        )
        print(f"config/schools.yaml: {len(schools)} schools")
    for k, v in existing_h.items():
        hackathons.setdefault(k, v)
    (CONFIG / "hackathons.yaml").write_text(
        "# Hackathons checked by the hackathon site checker. Seeded by hand (owner-approved), never from a\n"
        "# directory scrape. `reviewed: true` is the owner's sign-off after the audit.\n"
        + yaml.safe_dump({"hackathons": sorted(hackathons.values(), key=lambda h: h["name"].lower())},
                         sort_keys=False, allow_unicode=True, width=110)
    )
    print(f"config/hackathons.yaml: {len(hackathons)} hackathons")
    return 0


def add_hackathon(out: dict, existing: dict, hk: dict, host_school: str | None = None) -> None:
    url = hk.get("url") or hk.get("official_url")
    if not url or BLOCKED_HOSTS.search(host(url)):
        return
    hid = slug(hk["name"])
    if hid in existing:
        out[hid] = existing[hid]
        return
    city = hk.get("city")
    if city and "," in city:
        city = city.split(",")[0].strip()
    entry = {
        "id": hid,
        "name": hk["name"],
        "url": url,
        "host": host_school or hk.get("host") or hk.get("host_school"),
        "city": city,
        "region": hk.get("region") or ("CA-ON" if (hk.get("province") in (None, "ON", "Ontario")) else None),
        "country": "CA",
        "usual_month": hk.get("usual_month"),
        "reviewed": False,
        "enabled": hk.get("site_responds", True) is not False,
    }
    if hk.get("notes"):
        entry["notes"] = str(hk["notes"])[:300]
    out.setdefault(hid, entry)


if __name__ == "__main__":
    sys.exit(main())
