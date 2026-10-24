"""The daily review PR: a readable report plus fill-in stubs.

- reports/review.md lists every held-back item with its evidence and link, possible duplicates, records that
  disappeared from their source, and new volunteer / mentor / judge calls.
- config/manual/pending-review.yaml holds one stub per undated item. A reviewer fills in `start` (and anything
  else) to publish it, or sets `ignore: true` to drop it. Filled stubs move to config/manual/resolved.yaml on the
  next run, so the reviewer's work is never overwritten.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..config import CONFIG, ROOT
from ..pipeline import store

PENDING = CONFIG / "manual" / "pending-review.yaml"
RESOLVED = CONFIG / "manual" / "resolved.yaml"
IGNORED = store.REVIEW / "ignored.json"
REPORT = ROOT / "reports" / "review.md"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return (yaml.safe_load(path.read_text()) or {}).get("entries") or []


def _dump(path: Path, entries: list[dict], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = header + yaml.safe_dump({"entries": entries}, sort_keys=False, allow_unicode=True, width=110)
    store.write_if_changed(path, text)


def write_review() -> tuple[Path, int]:
    queue = store.load_json(store.REVIEW / "queue.json", {})
    ignored: list[str] = store.load_json(IGNORED, [])
    pending = _load(PENDING)
    resolved = _load(RESOLVED)

    # 1. Move filled-in or ignored stubs out of the pending file.
    still: list[dict] = []
    for e in pending:
        if e.get("ignore"):
            ignored.append(e["key"])
        elif e.get("start"):
            e.pop("evidence", None)
            e.pop("reasons", None)
            resolved.append(e)
        else:
            still.append(e)
    done = {e["key"] for e in resolved} | set(ignored)

    # 2. Add a stub for every new undated item.
    have = {e["key"] for e in still}
    for item in queue.get("items", []):
        if item["key"] in done or item["key"] in have:
            continue
        still.append({
            "key": item["key"],
            "title": item["title"],
            "url": item["url"],
            "type": None,
            "start": None,
            "end": None,
            "timezone": "America/Toronto",
            "roles": [{"role": "participant"}],
            "reasons": item["reasons"],
            "evidence": item["evidence"],
            "ignore": False,
        })
    live_keys = {i["key"] for i in queue.get("items", [])}
    still = [e for e in still if e["key"] in live_keys]  # the source fixed itself, or it was removed

    _dump(PENDING, still, "# Fill in `start` (ISO 8601, e.g. 2026-11-28T09:00) to publish an item, or set\n"
                         "# `ignore: true` to drop it. Generated daily by `openroster review`.\n")
    _dump(RESOLVED, resolved, "# Review items a person resolved. Loaded like any other manual entry.\n")
    store.write_if_changed(IGNORED, store.dump(sorted(set(ignored))))

    records = store.load_records()
    lines = ["# Daily review", "", f"Pending items: **{len(still)}** (fill them in `config/manual/pending-review.yaml`).", ""]
    if still:
        lines += ["## Held back: date or details unclear", ""]
        for e in still:
            lines += [f"### [{e['title']}]({e['url']})", f"- Why: {', '.join(e['reasons'])}",
                      f"- Evidence: > {e['evidence'][:300]}", ""]
    dupes = queue.get("possible_duplicates", [])
    if dupes:
        lines += ["## Possible duplicates (title similarity 80–90)", ""]
        for d in dupes:
            a, b = records.get(d["new"]), records.get(d["existing"])
            if a and b:
                lines.append(f"- `{a.id}` “{a.title}” vs `{b.id}` “{b.title}” ({d['score']})")
        lines.append("")
    missing = queue.get("flagged_missing", [])
    if missing:
        lines += ["## No longer listed by their source", ""]
        lines += [f"- `{rid}`" + (f" {records[rid].title}" if rid in records else "") for rid in missing] + [""]
    calls = queue.get("role_calls", [])
    if calls:
        lines += ["## New volunteer, mentor, judge and organizer calls", ""]
        for rid in calls:
            if rid in records:
                r = records[rid]
                roles = ", ".join(x.role for x in r.roles if x.role != "participant")
                lines.append(f"- [{r.title}]({r.sources[0].url}): {roles}")
        lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    store.write_if_changed(REPORT, "\n".join(lines) + "\n")
    to_review = len(still) + len(dupes) + len(missing) + len(calls)
    return REPORT, to_review
