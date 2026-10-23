"""Parse and validate GitHub issue-form bodies (submit, correct, takedown, permission), and apply them to config
and data files. The workflow commits the result to a branch and opens a PR; a maintainer merges it."""

from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from ..config import CONFIG, load_yaml
from ..model import Eligibility, Mode, OppType, Role
from ..pipeline import store
from ..pipeline.merge import title_score
from ..pipeline.normalize import slugify
from ..validate import EMAIL, PHONE

NO_RESPONSE = "_No response_"
SECTION = re.compile(r"^###\s+(.+?)\s*$", re.M)
LABELS = {
    "submit": {
        "Title": "title", "Type": "type", "Organizer": "organizer", "Official link": "url", "Start": "start",
        "End": "end", "Time zone": "timezone", "Format": "mode", "City": "city", "Province or state": "region",
        "Country": "country", "Ways to take part": "roles", "Deadlines": "deadlines", "Role links": "role_links",
        "Who can join": "eligibility", "Schools": "schools", "Cost": "cost", "Travel support offered?": "travel",
        "Short summary": "summary", "Confirmations": "confirm",
    },
    "correct": {
        "Listing ID": "opportunity_id", "Listing page": "page_url", "What is wrong?": "field",
        "Correct value": "value", "Where can we check this?": "evidence",
    },
    "takedown": {"Listing link or site address": "target", "Your relationship to it": "relationship",
                 "Anything else (optional)": "reason"},
    "permission": {"Site": "host", "Date granted": "granted", "Scope": "scope", "Evidence": "evidence"},
}
DT = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}):(\d{2}))?$")


def parse_sections(body: str) -> dict[str, str]:
    parts = SECTION.split(body.replace("\r\n", "\n"))
    out: dict[str, str] = {}
    for i in range(1, len(parts) - 1, 2):
        value = parts[i + 1].strip()
        out[parts[i].strip()] = "" if value == NO_RESPONSE else value
    return out


def checked(value: str) -> list[str]:
    return [m.strip() for m in re.findall(r"- \[[xX]\]\s*(.+)", value)]


def _dt(value: str, tz: str, end_of_day: bool = False) -> str | None:
    m = DT.match(value.strip())
    if not m:
        return None
    d, h, mi = m.groups()
    if h is None:
        return f"{d}T23:59" if end_of_day else d
    return f"{d}T{int(h):02d}:{mi}"


def _pairs(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower().replace(" ", "_").replace("-", "_")] = v.strip()
    return out


def _url_ok(u: str) -> bool:
    p = urlsplit(u)
    return p.scheme in ("http", "https") and bool(p.netloc)


def parse_submit(f: dict[str, str], issue: int) -> tuple[dict, list[str]]:
    errs: list[str] = []
    tz = f.get("timezone") or "America/Toronto"
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        errs.append(f"Unknown time zone `{tz}`.")
        tz = "America/Toronto"
    title = f.get("title", "").strip()
    if not 2 <= len(title) <= 200:
        errs.append("Title must be 2–200 characters.")
    if f.get("type") not in {t.value for t in OppType}:
        errs.append("Choose a type.")
    if f.get("mode") not in {m.value for m in Mode}:
        errs.append("Choose a format.")
    url = f.get("url", "").strip()
    if not _url_ok(url):
        errs.append("The official link must start with http:// or https://.")
    start = _dt(f.get("start", ""), tz)
    if not start:
        errs.append("Start must look like `2026-11-28 09:00` or `2026-11-28`.")
    end = _dt(f["end"], tz) if f.get("end") else None
    if f.get("end") and not end:
        errs.append("End must look like `2026-11-28 17:00`.")
    if start and end and end < start:
        errs.append("End is before start.")
    roles_named = checked(f.get("roles", "")) or ["participant"]
    valid_roles = {r.value for r in Role}
    deadlines = _pairs(f.get("deadlines", ""))
    links = _pairs(f.get("role_links", ""))
    roles = []
    for r in roles_named:
        if r not in valid_roles:
            continue
        role: dict = {"role": r}
        if r in deadlines:
            closes = _dt(deadlines[r], tz, end_of_day=True)
            if closes:
                role["closes"] = closes
            else:
                errs.append(f"Deadline for {r} must look like `2026-11-20 23:59` or `2026-11-20`.")
        if r in links:
            if _url_ok(links[r]):
                role["url"] = links[r]
            else:
                errs.append(f"Link for {r} is not a valid URL.")
        roles.append(role)
    for k in deadlines:
        if k not in roles_named:
            errs.append(f"A deadline was given for `{k}`, but that role is not ticked.")
    summary = " ".join(f.get("summary", "").split())
    if len(summary) > 200:
        errs.append(f"Summary is {len(summary)} characters; the limit is 200.")
    for field in ("title", "organizer", "summary"):
        if EMAIL.search(f.get(field, "")) or PHONE.search(f.get(field, "")):
            errs.append(f"Please remove personal contact details from {field}.")
    elig = [e for e in checked(f.get("eligibility", "")) if e in {x.value for x in Eligibility}] or ["unknown"]
    region = f.get("region", "").strip().upper()
    country = f.get("country", "CA") if f.get("country") in ("CA", "US") else None
    if region and not re.fullmatch(r"[A-Z]{2}", region):
        errs.append("Province or state must be two letters, like ON.")
    if not checked(f.get("confirm", "")):
        errs.append("Please tick the confirmation box.")

    entry = {
        "key": f"issue-{issue}",
        "title": title,
        "type": f.get("type"),
        "organizer": f.get("organizer", "").strip(),
        "url": url,
        "start": start,
        "end": end,
        "timezone": tz,
        "mode": f.get("mode"),
        "location": {k: v for k, v in {
            "city": f.get("city", "").strip() or None,
            "region": f"{country}-{region}" if region and country else None,
            "country": country,
        }.items() if v},
        "roles": roles,
        "eligibility": elig,
        "cost": {"kind": f.get("cost", "unknown")},
        "summary": summary or None,
        "submitted_in": f"#{issue}",
    }
    names = [s.strip() for s in f.get("schools", "").split(",") if s.strip()]
    if names:
        ids, unknown = match_schools(names)
        entry["schools"] = ids or ["open_to_all"]
        if unknown:
            errs.append("Unknown school(s): " + ", ".join(unknown) + ". Use the full name, e.g. Brock University.")
    if f.get("travel") == "yes":
        entry["tags"] = ["travel_support"]
    return entry, errs


def match_schools(names: list[str]) -> tuple[list[str], list[str]]:
    schools = load_yaml("schools.yaml").get("schools", [])
    ids: list[str] = []
    unknown: list[str] = []
    for n in names:
        key = n.lower()
        hit = next((s["id"] for s in schools
                    if key in {s["id"], s["name"].lower(), *(a.lower() for a in s.get("aliases", []))}), None)
        hit = hit or next((s["id"] for s in schools if key in s["name"].lower()), None)
        (ids if hit else unknown).append(hit or n)
    return ids, unknown


def duplicates(entry: dict) -> list[str]:
    out = []
    for r in store.load_records().values():
        if entry.get("start") and r.start.date().isoformat() == entry["start"][:10] and title_score(r.title, entry["title"]) >= 80:
            out.append(r.id)
    return out


def parse_issue(body: str, kind: str = "submit", issue_number: int = 0, write: bool = False) -> dict:
    sections = parse_sections(body)
    labels = LABELS[kind]
    f = {labels[k]: v for k, v in sections.items() if k in labels}
    result: dict = {"ok": False, "kind": kind, "errors": [], "warnings": [], "path": None}
    if kind == "submit":
        entry, errs = parse_submit(f, issue_number)
        result["errors"] = errs
        dupes = duplicates(entry) if not errs else []
        if dupes:
            result["warnings"].append("Possible duplicate of: " + ", ".join(f"`{d}`" for d in dupes))
        result["entry"] = entry
        path = CONFIG / "submissions" / f"issue-{issue_number}-{slugify(entry['title'], 40)}.yaml"
        result["path"] = str(path.relative_to(CONFIG.parent))
        if not errs and write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# From issue #{issue_number}\n" + yaml.safe_dump(entry, sort_keys=False, allow_unicode=True))
    elif kind == "correct":
        result.update(apply_correction(f, write))
    elif kind == "takedown":
        result.update(apply_takedown(f, write))
    elif kind == "permission":
        result.update(apply_permission(f, write))
    result["ok"] = not result["errors"]
    return result


FIELD_MAP = {"title": "title", "start": "start", "end": "end", "type": "type", "mode": "mode"}


def apply_correction(f: dict[str, str], write: bool) -> dict:
    errs: list[str] = []
    rid = f.get("opportunity_id", "").strip()
    records = store.load_records()
    if rid not in records:
        errs.append(f"No current listing has the ID `{rid}`.")
    if not _url_ok(f.get("evidence", "")):
        errs.append("Please link to the official page that shows the correct detail.")
    field, value = f.get("field", ""), f.get("value", "").strip()
    patch: dict = {}
    if not errs:
        rec = records[rid]
        if field in ("start", "end"):
            v = _dt(value, rec.timezone)
            if not v:
                errs.append("Dates must look like `2026-11-28 09:00`.")
            else:
                patch[field] = datetime.fromisoformat(v).replace(tzinfo=ZoneInfo(rec.timezone)).isoformat()
        elif field == "cancelled":
            patch["status"] = "cancelled"
        elif field == "registration link":
            if not _url_ok(value):
                errs.append("The link must start with http:// or https://.")
            patch["registration"] = {"route": "public_link", "url": value}
        elif field == "city":
            patch["location"] = {**rec.location.model_dump(), "city": value}
        elif field == "deadline":
            pairs = _pairs(value)
            roles = [r.model_dump(mode="json") for r in rec.roles]
            for r in roles:
                if r["role"] in pairs and (d := _dt(pairs[r["role"]], rec.timezone, end_of_day=True)):
                    r["closes"] = datetime.fromisoformat(d).replace(tzinfo=ZoneInfo(rec.timezone)).isoformat()
            patch["roles"] = roles
        elif field in FIELD_MAP:
            patch[FIELD_MAP[field]] = value
        else:
            errs.append("This kind of correction needs a maintainer; it has been left for review.")
    if not errs and write:
        path = CONFIG / "overrides.yaml"
        doc = yaml.safe_load(path.read_text()) if path.exists() else {}
        doc = doc or {}
        doc["overrides"] = doc.get("overrides") or {}
        doc["overrides"].setdefault(rid, {}).update(patch)
        path.write_text("# Owner-approved corrections, keyed by record id. Written by the correction workflow.\n"
                        + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    return {"errors": errs, "patch": patch, "path": "config/overrides.yaml"}


def apply_takedown(f: dict[str, str], write: bool) -> dict:
    target = f.get("target", "").strip()
    errs: list[str] = []
    td = store.takedowns()
    m = re.search(r"/o/([a-z0-9-]+)/?", target)
    if m:
        td["ids"] = sorted(set(td["ids"]) | {m.group(1)})
        what = f"listing `{m.group(1)}`"
    else:
        host = (urlsplit(target if "://" in target else f"https://{target}").hostname or "").lower()
        if not host or "." not in host:
            errs.append("Give a listing link (…/o/<id>/) or a site domain like example.com.")
            what = ""
        else:
            td["hosts"] = sorted(set(td["hosts"]) | {host, host.removeprefix("www.")})
            what = f"site `{host}`"
    if not errs and write:
        store.write_if_changed(store.TAKEDOWNS, store.dump(td))
    return {"errors": errs, "what": what, "path": "data/takedowns.json"}


def apply_permission(f: dict[str, str], write: bool) -> dict:
    host = f.get("host", "").strip().lower()
    errs: list[str] = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", f.get("granted", "").strip()):
        errs.append("Date granted must be YYYY-MM-DD.")
    path = CONFIG / "known_verdicts.yaml"
    doc = yaml.safe_load(path.read_text())
    entry = next((v for v in doc["verdicts"] if host in v["hosts"]), None)
    if entry is None or entry["verdict"] != "permission_required":
        errs.append(f"`{host}` is not listed as permission_required in config/known_verdicts.yaml.")
    if not errs and write and entry is not None:
        entry["permission"] = {"granted": f["granted"].strip(), "scope": f.get("scope", "").strip(),
                               "evidence": f.get("evidence", "").strip()}
        path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110))
    return {"errors": errs, "path": "config/known_verdicts.yaml"}


def comment_for(result: dict) -> str:
    if result["ok"]:
        lines = ["Thanks! This passed the automatic checks. A pull request will be opened for a maintainer to approve."]
        lines += [f"- ⚠️ {w}" for w in result.get("warnings", [])]
        return "\n".join(lines)
    return "Thanks! A few things need fixing before this can be added (edit the issue and the bot re-checks):\n\n" + \
        "\n".join(f"- {e}" for e in result["errors"])


def as_json(result: dict) -> str:
    return json.dumps(result, indent=2, default=str)
