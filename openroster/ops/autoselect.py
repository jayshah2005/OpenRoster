"""Rule-based selectors for approved HTML sources that have none yet.

For each source with `adapter: html`, `reviewed: true` and no `options.item`, fetch its page once through the polite
fetcher, try the selector suggestions from ops/selectors.py, and keep the first one that turns at least two blocks
into dated events. The winning selectors are written into the source's config (comments kept), the source is
enabled, and a sanitized copy of the page is saved as its test fixture. A person reviews the result in a PR.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from ..adapters.html import parse_html_list
from ..config import CONFIG, ROOT, Source, load_sources
from ..fetch import BudgetExceeded, Fetcher, FetchError, FetchRefused
from .sanitize import sanitize
from .selectors import suggest

FIXTURES = ROOT / "tests" / "fixtures" / "sources"
MIN_DATED = 2
GENERIC = {"div", "span", "section", "p", "a"}


@dataclass
class Outcome:
    source_id: str
    ok: bool
    detail: str


_DATE_IN_TITLE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.? \d{1,2}\b|\b\d{1,2}:\d{2}\b", re.I)

# Section headings and labels that a too-wide selector picks up instead of event names.
_GENERIC_TITLE = re.compile(r"^(?:(?:upcoming|featured|past|all|our|more|latest)\s+)?(?:events?|news|calendar|always on)$", re.I)


def clean_titles(titles: list[str]) -> bool:
    """Titles that look like titles: short, and without dates or times in them. Long titles with dates mean the
    selector grabbed the whole block (date, place and description), and we never store copied descriptions."""
    if not titles:
        return False
    lengths = sorted(len(t) for t in titles)
    dated = sum(1 for t in titles if _DATE_IN_TITLE.search(t))
    generic = sum(1 for t in titles if _GENERIC_TITLE.match(t.strip()))
    distinct = len({t.strip().lower() for t in titles})
    return (lengths[len(lengths) // 2] <= 80 and dated <= len(titles) // 4 and generic == 0
            and distinct >= 0.8 * len(titles))  # repeated titles mean we picked a label, not the event name


def candidates_for(html: str, source: Source) -> tuple[dict | None, int]:
    """The best working selector set for this page, and how many dated events it found."""
    best: tuple[dict | None, int] = (None, 0)
    for s in suggest(html, limit=8):
        options = {**source.options, "item": s.item}
        if s.title:
            options["title"] = s.title
        if s.item in GENERIC:  # a bare `div` matches nested wrappers: duplicates and page chrome
            continue
        trial = source.model_copy(update={"options": options})
        res = parse_html_list(html, source.url, trial)
        if not clean_titles([c.title for c in res.candidates]):
            continue
        dated = sum(1 for c in res.candidates if c.start is not None)
        if dated > best[1]:
            best = ({"item": s.item, **({"title": s.title} if s.title else {})}, dated)
    return best


def _write_options(source_id: str, chosen: dict) -> bool:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # never re-wrap lines, so the PR diff shows only the real changes
    y.indent(mapping=2, sequence=2, offset=0)
    for path in sorted((CONFIG / "sources").glob("*.yaml")):
        doc = y.load(path.read_text())
        for entry in doc.get("sources") or []:
            if entry.get("id") == source_id:
                opts = entry.setdefault("options", {})
                opts.update(chosen)
                entry["enabled"] = True
                if str(entry.get("notes", "")).startswith("NEEDS SELECTORS"):
                    entry["notes"] = "Selectors proposed by `openroster autoselect`; check the fixture test." + \
                        str(entry["notes"])[len("NEEDS SELECTORS before enabling."):]
                with path.open("w") as fh:
                    y.dump(doc, fh)
                return True
    return False


def autoselect(only: set[str] | None = None, fetcher: Fetcher | None = None) -> list[Outcome]:
    fetcher = fetcher or Fetcher()
    out: list[Outcome] = []
    for src in load_sources():
        # `autoselect: false` marks pages a person decided rules can't handle well (see the source's notes).
        if src.adapter != "html" or not src.reviewed or "item" in src.options or src.options.get("autoselect") is False:
            continue
        if only and src.id not in only:
            continue
        try:
            # One page, but redirect hops count against the budget too (http -> https -> www is common).
            fetcher.set_budget(src.id, 3)
            html = fetcher.get(src.url, source_id=src.id).text
        except (FetchError, FetchRefused, BudgetExceeded) as e:
            out.append(Outcome(src.id, False, f"could not fetch: {e}"))
            continue
        chosen, dated = candidates_for(html, src)
        if chosen is None or dated < MIN_DATED:
            out.append(Outcome(src.id, False, f"no selector found {dated} dated events (needs a person or the AI helper)"))
            continue
        _write_options(src.id, chosen)
        FIXTURES.mkdir(parents=True, exist_ok=True)
        fixture = FIXTURES / f"{src.id}.html"
        fixture.write_text(html)
        sanitize(fixture)
        out.append(Outcome(src.id, True, f"item={chosen['item']!r}, {dated} dated events"))
    return out


def report(outcomes: list[Outcome], path: Path = ROOT / "reports" / "autoselect.md") -> None:
    lines = ["# Selector proposals", "", "Rule-based selectors for approved HTML sources. Each one is covered by "
             "`tests/test_html_sources.py` against the saved page.", ""]
    lines += [f"- {'✅' if o.ok else '⚠️'} `{o.source_id}`: {o.detail}" for o in outcomes] or ["- Nothing to do."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[4:]), file=sys.stderr)
