"""Matching new candidates to existing records, merging duplicates, tracking moves, misses and archiving."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from rapidfuzz import fuzz

from ..model import HistoryEntry, Opportunity, SourceRef

PRIORITY = {"manual": 5, "submission": 4, "ics": 3, "tribe": 3, "localist": 3, "jsonld": 3, "sitemap": 3,
            "api": 3, "rss": 3, "hackathon_site": 2, "html": 2, "headless": 1}
MERGE_AT = 90
REVIEW_AT = 80
MISSES_BEFORE_REVIEW = 2


def _norm_title(t: str) -> str:
    t = re.sub(r"\b20\d{2}\b", "", t.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def title_score(a: str, b: str) -> float:
    na, nb = _norm_title(a), _norm_title(b)
    score = fuzz.token_sort_ratio(na, nb)
    # A full subset ("HerHacks" vs "BMO HerHacks Hackathon") counts only for titles with >= 3 words.
    if min(len(na.split()), len(nb.split())) >= 3:
        score = max(score, fuzz.token_set_ratio(na, nb))
    return score


def same_place(a: Opportunity, b: Opportunity) -> bool:
    if a.mode == "online" or b.mode == "online":
        return a.mode == b.mode or "unknown" in (a.mode, b.mode)
    ca, cb = (a.location.city or "").lower(), (b.location.city or "").lower()
    return not ca or not cb or ca == cb


def close_in_time(a: Opportunity, b: Opportunity) -> bool:
    return abs(a.start - b.start) <= timedelta(days=1)


def priority(o: Opportunity) -> int:
    return max(PRIORITY.get(v, 0) for v in o.obtained_via)


@dataclass
class MergeState:
    records: dict[str, Opportunity]
    keys: dict[str, str]                 # candidate key -> record id
    aliases: dict[str, str]              # old id -> canonical id
    misses: dict[str, int]
    seen: set[str] = field(default_factory=set)
    possible_dupes: list[tuple[str, str, float]] = field(default_factory=list)

    def find_match(self, new: Opportunity) -> tuple[Opportunity | None, float]:
        best: tuple[Opportunity | None, float] = (None, 0.0)
        for r in self.records.values():
            if r.id == new.id or not close_in_time(r, new) or not same_place(r, new):
                continue
            if _same_url(r, new):
                return r, 100.0
            s = title_score(r.title, new.title)
            if s > best[1]:
                best = (r, s)
        return best


def _same_url(a: Opportunity, b: Opportunity) -> bool:
    def canon(u: str) -> str:
        p = urlsplit(u)
        return f"{p.hostname}{p.path.rstrip('/')}".lower()

    a_urls = {canon(s.url) for s in a.sources}
    b_urls = {canon(s.url) for s in b.sources}
    # Listing pages are shared by many events; a URL match only counts when it is a per-event page.
    generic = {canon(s.url) for s in a.sources if s.url.rstrip("/").endswith(("/events", "/calendar"))}
    return bool((a_urls & b_urls) - generic) and a.start.date() == b.start.date()


def update_record(old: Opportunity, new: Opportunity, now: datetime, same_source: bool) -> Opportunity:
    """Fold `new` into `old`. Same-source updates may move dates; cross-source merges only fill gaps,
    unless the new source has higher priority."""
    data = old.model_dump()
    history = list(old.history)
    if same_source and abs(new.start - old.start) > timedelta(minutes=1):
        history.append(HistoryEntry(at=now, field="start", old=old.start.isoformat(), new=new.start.isoformat()))
        data["start"], data["end"] = new.start, new.end
        data["status"] = "moved"
    if new.status == "cancelled" and old.status != "cancelled" and (same_source or priority(new) >= priority(old)):
        history.append(HistoryEntry(at=now, field="status", old=old.status, new="cancelled"))
        data["status"] = "cancelled"
    elif old.status == "needs_review" and same_source:
        data["status"] = "scheduled"
        data["review"] = None
    take_new = priority(new) > priority(old) or (same_source and priority(new) == priority(old))
    for f in ("title", "type", "mode", "registration", "cost", "summary", "all_day", "end"):
        if take_new and getattr(new, f) not in (None, "", "unknown"):
            data[f] = getattr(new, f).model_dump() if hasattr(getattr(new, f), "model_dump") else getattr(new, f)
    loc = data["location"]
    for k, v in new.location.model_dump().items():
        if v and (take_new or not loc.get(k)):
            loc[k] = v
    if new.geo and (take_new or not old.geo):
        data["geo"] = new.geo.model_dump()
        data["near_schools"] = [n.model_dump() for n in new.near_schools]
    # Roles: union by role name; known dates win over unknown ones.
    roles = {r.role: r.model_dump() for r in old.roles}
    for r in new.roles:
        cur = roles.get(r.role)
        if cur is None:
            roles[r.role] = r.model_dump()
        else:
            for k in ("opens", "closes", "url", "evidence"):
                if getattr(r, k) and (take_new or not cur.get(k)):
                    cur[k] = getattr(r, k)
            if r.status != "unknown" and (take_new or cur["status"] == "unknown"):
                cur["status"] = r.status
    data["roles"] = list(roles.values())
    data["tags"] = list(dict.fromkeys([*old.tags, *new.tags]))
    schools = set(old.schools) | set(new.schools)
    data["schools"] = ["open_to_all"] if "open_to_all" in schools else sorted(schools)
    # Timestamps advance at most once per day, so a scrape that finds nothing new produces no diff.
    srcs = {(s.source_id, s.url): s for s in old.sources}
    for s in new.sources:
        prev = srcs.get((s.source_id, s.url))
        if prev is None or prev.fetched_at.date() != now.date():
            srcs[(s.source_id, s.url)] = SourceRef(url=s.url, adapter=s.adapter, source_id=s.source_id,
                                                   fetched_at=now)
    data["sources"] = [s.model_dump() for s in srcs.values()]
    data["obtained_via"] = sorted(set(old.obtained_via) | set(new.obtained_via))
    data["history"] = [h.model_dump() for h in history]
    if old.last_seen.date() != now.date():
        data["last_seen"] = now
        data["last_verified"] = now
    return Opportunity.model_validate(data)


def ingest(state: MergeState, key: str, new: Opportunity, now: datetime) -> str:
    """Insert or merge one normalized candidate. Returns the canonical record id."""
    rid = state.keys.get(key)
    rid = state.aliases.get(rid, rid) if rid else None
    if rid and rid in state.records:
        state.records[rid] = update_record(state.records[rid], new, now, same_source=True)
    else:
        match, score = state.find_match(new)
        if match is not None and score >= MERGE_AT:
            rid = match.id
            state.records[rid] = update_record(match, new, now, same_source=False)
        else:
            if match is not None and score >= REVIEW_AT:
                state.possible_dupes.append((new.id, match.id, score))
            rid = new.id
            if rid in state.records:  # id collision from an identical title+month+hash: keep the existing one
                state.records[rid] = update_record(state.records[rid], new, now, same_source=True)
            else:
                state.records[rid] = new
    state.keys[key] = rid
    state.seen.add(rid)
    state.misses.pop(rid, None)
    return rid


def apply_misses(state: MergeState, ran_ok: set[str], now: datetime) -> list[str]:
    """Records whose every source ran successfully but did not list them get a miss; two misses -> review."""
    flagged: list[str] = []
    for rid, r in list(state.records.items()):
        if rid in state.seen or r.status in ("past", "needs_review"):
            continue
        srcs = {s.source_id for s in r.sources}
        if not srcs or not srcs <= ran_ok:
            continue
        state.misses[rid] = state.misses.get(rid, 0) + 1
        if state.misses[rid] >= MISSES_BEFORE_REVIEW and r.start > now:
            data = r.model_dump()
            data["status"] = "needs_review"
            data["review"] = {"reasons": ["no longer listed by its source (possibly cancelled or moved)"],
                              "evidence": [{"text": "missing from the last 2 successful fetches", "url": s.url}
                                           for s in r.sources][:3]}
            state.records[rid] = Opportunity.model_validate(data)
            flagged.append(rid)
    return flagged


def is_past(o: Opportunity, now: datetime) -> bool:
    return (o.end or o.start) < now - timedelta(hours=12)
