"""Build preview data from saved test fixtures only (no network). Used to look at the site before any source is
approved. Writes to the folder in OPENROSTER_DATA (required) so the real data/ folder is untouched.

Usage: OPENROSTER_DATA=/tmp/preview uv run python scripts/preview_from_fixtures.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if not os.environ.get("OPENROSTER_DATA"):
    sys.exit("set OPENROSTER_DATA to a scratch folder")

from openroster.adapters.api import load_manual, parse_hackclub  # noqa: E402
from openroster.adapters.campus import parse_tribe  # noqa: E402
from openroster.adapters.html import parse_html_list  # noqa: E402
from openroster.adapters.ics import parse_ics  # noqa: E402
from openroster.config import Source, load_sources  # noqa: E402
from openroster.pipeline import run as run_mod  # noqa: E402

FX = ROOT / "tests" / "fixtures"
# Frozen clock: the fixtures were captured on this date, so CI stays green as real time moves on.
NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)
by_id = {s.id: s for s in load_sources()}


def src(sid: str, adapter: str, **kw) -> Source:
    return by_id.get(sid) or Source(id=sid, name=kw.pop("name", sid), adapter=adapter, url="https://example.org",
                                    owner=sid, **kw)


extra = []
for sid in ("bmo-student-events", "bmo-virtual-workshops", "scotiabank-campus-events"):
    s = by_id[sid]
    extra.append((s, parse_html_list((FX / f"sources/{sid}.html").read_text(), s.url, s)))
vector = src("vector-institute-events", "tribe")
cands, _, _ = parse_tribe(json.loads((FX / "tribe/vector.json").read_text()), vector)
from openroster.adapters.base import AdapterResult  # noqa: E402

extra.append((vector, AdapterResult(candidates=cands)))
hc = src("hackclub-hackathons-api-upcoming", "hackclub")
extra.append((hc, parse_hackclub(json.loads((FX / "api/hackclub.json").read_text()), hc)))
luma = next((s for s in by_id.values() if "cutc" in s.id), None) or src("luma-cutc", "ics")
extra.append((luma, parse_ics((FX / "ics/luma-cutc.ics").read_text(), luma, now=NOW)))

run_mod.load_sources = lambda: []  # no live fetching in a preview
rep = run_mod.run(extra=extra, include_hackathons=False, now=NOW)
print(f"preview: {len(rep.new)} records, {len(rep.review)} review items, manual={load_manual().raw_count}")
