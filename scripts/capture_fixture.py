"""Save one page of a configured HTML source as a test fixture, using the polite fetcher (robots.txt, rate limit,
known verdicts all apply). Used when selectors change, by people and by the AI repair job.

Usage: uv run python scripts/capture_fixture.py <source-id>
Writes a sanitized tests/fixtures/sources/<source-id>.html, which tests/test_html_sources.py parses with the source's config.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from openroster.config import load_sources  # noqa: E402
from openroster.fetch import Fetcher  # noqa: E402
from scripts.sanitize_fixture import sanitize  # noqa: E402


def main(sid: str) -> int:
    src = next((s for s in load_sources() if s.id == sid), None)
    if src is None or src.adapter not in ("html", "headless"):
        print(f"{sid}: not an HTML source", file=sys.stderr)
        return 2
    if not src.reviewed:
        print(f"{sid}: not reviewed by the owner yet; refusing to fetch", file=sys.stderr)
        return 2
    page = Fetcher().get(src.url, source_id=src.id)
    out = ROOT / "tests" / "fixtures" / "sources" / f"{sid}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.text)
    sanitize(out)  # keep structure and facts; drop third-party prose before it can be committed
    print(f"saved {out.relative_to(ROOT)} ({len(page.text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) == 2 else 2)
