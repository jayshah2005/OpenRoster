"""Every HTML source that has a saved page in tests/fixtures/sources/ must still parse with its configured
selectors. A broken selector (or a broken fixture) fails CI."""

from pathlib import Path

import pytest

from openroster.adapters.html import parse_html_list
from openroster.config import load_sources

FX = Path(__file__).parent / "fixtures" / "sources"
SOURCES = {s.id: s for s in load_sources() if s.adapter in ("html", "headless")}
CASES = sorted(p.stem for p in FX.glob("*.html")) if FX.exists() else []


@pytest.mark.parametrize("sid", CASES)
def test_source_fixture_parses(sid):
    assert sid in SOURCES, f"fixture for unknown or non-HTML source {sid}"
    s = SOURCES[sid]
    res = parse_html_list((FX / f"{sid}.html").read_text(), s.url, s)
    assert res.raw_count > 0, "the item selector matches nothing"
    assert res.candidates, "no items survived the filters"
    dated = [c for c in res.candidates if c.start is not None]
    assert len(dated) >= len(res.candidates) / 2, "most items should have a parseable date"
