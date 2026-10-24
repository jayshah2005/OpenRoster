"""One scrape run: fetch every runnable source, normalize, merge, archive, write, and record source health."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from ..adapters import ADAPTERS
from ..adapters.api import load_manual, load_submissions
from ..adapters.base import AdapterResult, Candidate
from ..config import Source, load_sources, load_yaml
from ..fetch import Fetcher, FetchError, FetchRefused
from ..model import Opportunity
from ..parallel import by_host
from ..validate import pii_problems
from . import store
from .merge import MergeState, apply_misses, ingest, is_past
from .normalize import ReviewItem, candidate_key, host_of, normalize

log = logging.getLogger("openroster")


@dataclass
class SourceHealth:
    ok: bool
    count: int
    raw_count: int
    pages: int
    error: str | None = None
    fingerprint: str | None = None
    refused: bool = False


@dataclass
class RunReport:
    started: str
    health: dict[str, SourceHealth] = field(default_factory=dict)
    new: list[str] = field(default_factory=list)
    updated: int = 0
    archived: list[str] = field(default_factory=list)
    review: list[dict] = field(default_factory=list)
    flagged_missing: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def run_source(source: Source, fetcher: Fetcher) -> tuple[AdapterResult | None, SourceHealth]:
    adapter = ADAPTERS.get(source.adapter)
    if adapter is None:
        return None, SourceHealth(False, 0, 0, 0, f"unknown adapter {source.adapter}")
    fetcher.set_budget(source.id, source.page_budget)
    try:
        res = adapter.run(source, fetcher)
    except FetchRefused as e:
        return None, SourceHealth(False, 0, 0, 0, str(e), refused=True)
    except (FetchError, ValueError, KeyError) as e:
        return None, SourceHealth(False, 0, 0, 0, f"{type(e).__name__}: {e}")
    except Exception as e:  # an adapter bug must not stop other sources; it is surfaced as a health issue
        log.exception("adapter crashed for %s", source.id)
        return None, SourceHealth(False, 0, 0, 0, f"crash: {type(e).__name__}: {e}")
    return res, SourceHealth(True, len(res.candidates), res.raw_count, res.pages,
                             "; ".join(res.errors) or None, res.fingerprint)


def suppressed(c: Candidate, td: dict[str, list[str]]) -> bool:
    return c.url in td["urls"] or host_of(c.url) in td["hosts"]


def run(
    only: set[str] | None = None,
    fetcher: Fetcher | None = None,
    extra: list[tuple[Source | None, AdapterResult]] | None = None,
    now: datetime | None = None,
    include_hackathons: bool = True,
) -> RunReport:
    now = now or datetime.now(UTC)
    report = RunReport(started=now.isoformat())
    sources = load_sources()
    by_id = {s.id: s for s in sources}

    results: list[tuple[Source | None, AdapterResult]] = []
    todo = []
    for s in sources:
        if only and s.id not in only:
            continue
        if not s.runnable:
            report.skipped.append(s.id)
            continue
        todo.append(s)

    def one(s: Source, f: Fetcher) -> tuple[AdapterResult | None, SourceHealth]:
        log.info("source %s (%s)", s.id, s.adapter)
        return run_source(s, f)

    # Sites run in parallel, one worker per host (parallel.py); a given fetcher (tests) runs everything in order.
    done = [(s, one(s, fetcher)) for s in todo] if fetcher else by_host(todo, url_of=lambda s: s.url, work=one)
    for s, (res, health) in done:
        report.health[s.id] = health
        if res:
            results.append((s, res))
    if not only:
        results.append((None, load_manual()))
        results.append((None, load_submissions()))
        if include_hackathons:
            from ..hackathons import check_all

            hres, hhealth = check_all(fetcher)
            report.health.update(hhealth)
            results.append((None, hres))
    results.extend(extra or [])

    state = MergeState(
        records=store.load_records(),
        keys=store.load_json(store.KEYS, {}),
        aliases=store.load_json(store.ALIASES, {}),
        misses=store.load_json(store.STATE, {}).get("misses", {}),
    )
    td = store.takedowns()
    before = set(state.records)
    review: list[ReviewItem] = []
    for src, res in results:
        for c in res.candidates:
            if suppressed(c, td):
                continue
            source = src or by_id.get(c.source_id)
            try:
                out = normalize(c, source, now)
            except ValueError as e:  # schema rejected it: send to review instead of guessing
                review.append(ReviewItem(candidate_key(c), c.source_id, c.title, c.url, [f"invalid: {e}"[:200]],
                                         (c.date_evidence or c.text)[:300]))
                continue
            if isinstance(out, ReviewItem):
                review.append(out)
                continue
            if out.id in td["ids"] or (out.end or out.start) < now:
                continue
            # Something that looks like personal data (an email, phone or handle in a stored field) goes to a
            # person instead of the site, so one bad item can't block the whole run at the validate step.
            pii = pii_problems(out.model_dump(mode="json"), out.id)
            if pii:
                review.append(ReviewItem(candidate_key(c), c.source_id, c.title, c.url, pii[:3], c.title[:300]))
                continue
            ingest(state, candidate_key(c), out, now)

    ran_ok = {sid for sid, h in report.health.items() if h.ok}
    ran_ok |= {f"manual:{f}" for f in _stems("manual")} | {f"submission:{f}" for f in _stems("submissions")}
    report.flagged_missing = apply_misses(state, ran_ok, now)

    # Archive past records.
    live: dict[str, Opportunity] = {}
    for rid, r in state.records.items():
        if rid in td["ids"]:
            continue
        if is_past(r, now):
            data = r.model_dump()
            data["status"] = "past"
            past = Opportunity.model_validate(data)
            store.write_if_changed(store.ARCHIVE / f"{past.start:%Y}" / f"{rid}.json", store.record_json(past))
            report.archived.append(rid)
        else:
            live[rid] = r

    # Owner-approved corrections (from correction issues) win over any source.
    for rid, fields in (load_yaml("overrides.yaml").get("overrides") or {}).items():
        rid = state.aliases.get(rid, rid)
        if rid in live:
            data = live[rid].model_dump()
            data.update(fields)
            live[rid] = Opportunity.model_validate(data)

    # Write live records; remove files for records that left the live set.
    for rid, r in live.items():
        if store.write_if_changed(store.RECORDS / f"{rid}.json", store.record_json(r)) and rid in before:
            report.updated += 1
    for f in store.RECORDS.glob("*.json"):
        if f.stem not in live:
            f.unlink()
    report.new = sorted(set(live) - before)

    store.write_if_changed(store.KEYS, store.dump(dict(sorted(state.keys.items()))))
    store.write_if_changed(store.ALIASES, store.dump(state.aliases))
    prev_state = store.load_json(store.STATE, {})
    sources_state = prev_state.get("sources", {})
    # Only values that change when something actually happens are stored (dates, not times; a capped
    # streak), so a quiet run leaves this file untouched and produces no commit.
    from ..ops.health import HEALTHY_RUNS_TO_CLOSE

    for sid, h in report.health.items():
        prev = sources_state.get(sid, {})
        raw = h.raw_count if h.ok else prev.get("raw_count", 0)
        problem = (not h.ok) or (raw == 0 and prev.get("last_nonzero", 0) > 0) or (
            bool(h.fingerprint) and bool(prev.get("fingerprint")) and h.fingerprint != prev.get("fingerprint"))
        sources_state[sid] = {
            "ok": h.ok,
            "count": h.count if h.ok else prev.get("count", 0),
            "raw_count": raw,
            "last_nonzero": raw if raw > 0 else prev.get("last_nonzero", 0),
            "fingerprint": h.fingerprint or prev.get("fingerprint"),
            "prev_fingerprint": prev.get("fingerprint") if h.fingerprint != prev.get("fingerprint") else
            prev.get("prev_fingerprint"),
            "error": h.error,
            "refused": h.refused,
            "last_ok": now.date().isoformat() if h.ok else prev.get("last_ok"),
            "consecutive_failures": 0 if h.ok else prev.get("consecutive_failures", 0) + 1,
            "healthy_streak": 0 if problem else min(prev.get("healthy_streak", 0) + 1, HEALTHY_RUNS_TO_CLOSE),
        }
    # Pipeline-level numbers for the red-flag checks (ops/health.py) and the public status page.
    pipeline = {
        "configured": len(sources),
        "approved": sum(1 for s in sources if s.reviewed),
        "runnable": sum(1 for s in sources if s.runnable),
        "failing": sum(1 for h in report.health.values() if not h.ok),
        "listings": len(live),
        "held_for_review": len(review),
        "last_run": now.date().isoformat(),
    }
    store.write_if_changed(store.STATE, store.dump({"misses": state.misses, "sources": sources_state, "pipeline": pipeline}))

    ignored = set(store.load_json(store.REVIEW / "ignored.json", []))
    review_doc: dict[str, list] = {
        "items": [asdict(r) for r in sorted(review, key=lambda r: r.key) if r.key not in ignored],
        "possible_duplicates": [{"new": a, "existing": b, "score": round(s, 1)} for a, b, s in state.possible_dupes],
        "flagged_missing": report.flagged_missing,
        "role_calls": sorted(
            rid for rid in report.new
            if any(r.role != "participant" for r in live[rid].roles)
        ),
    }
    store.write_if_changed(store.REVIEW / "queue.json", store.dump(review_doc))
    report.review = review_doc["items"]  # list of dicts
    return report


def _stems(folder: str) -> list[str]:
    from ..config import CONFIG

    return [f.stem for f in (CONFIG / folder).glob("*.yaml")]
