"""Make a saved page safe to commit to a public repo: keep structure and facts, drop third-party prose.

Fixtures exist to test selectors and date parsing, so titles, dates, times, places and links stay. Long prose
(event descriptions) is replaced with neutral placeholder text of similar length, scripts/styles/images are
removed, and email addresses are masked. This keeps us from republishing other sites' content.

Usage: uv run python scripts/sanitize_fixture.py <file> [<file> ...]   (HTML, RSS/XML or JSON; edits in place)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PLACEHOLDER = "Placeholder description text."
LONG = 140  # characters: longer text runs are treated as prose


def filler(n: int) -> str:
    return (PLACEHOLDER + " ") * max(1, n // (len(PLACEHOLDER) + 1))


def sanitize_html(text: str) -> str:
    text = re.sub(r"<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>", "", text, flags=re.S | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<svg\b[^>]*>.*?</svg>", "", text, flags=re.S | re.I)
    text = re.sub(r"<(img|source|picture|video|iframe)\b[^>]*>", "", text, flags=re.I)
    text = re.sub(r"\s(srcset|data-src|style)=\"[^\"]*\"", "", text)

    def prose(m: re.Match[str]) -> str:
        s = m.group(1)
        return f">{filler(len(s)).strip()}<" if len(s.strip()) > LONG else m.group(0)

    text = re.sub(rf">([^<>]{{{LONG},}})<", prose, text)
    return EMAIL.sub("hidden@example.org", text)


def sanitize_xml(text: str) -> str:
    # Engage RSS: keep the h-event title/time/location markup, drop the description body and images.
    text = re.sub(r'<div class="p-description description">.*?</div>\s*(?=<div>)',
                  f'<div class="p-description description"><p>{PLACEHOLDER}</p></div>\n', text, flags=re.S)
    text = re.sub(r"<enclosure [^>]*/>", "", text)
    text = re.sub(r"<author>.*?</author>\s*", "", text, flags=re.S)
    return sanitize_html(text)


def sanitize_json(obj: object) -> object:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ("contactDetails", "author", "_links", "yoast_head", "yoast_head_json"):
                continue
            if k in ("content", "description", "excerpt") and isinstance(v, (str, dict)):
                out[k] = {"rendered": f"<p>{PLACEHOLDER}</p>"} if isinstance(v, dict) else PLACEHOLDER
                continue
            out[k] = sanitize_json(v)
        return out
    if isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    if isinstance(obj, str):
        return EMAIL.sub("hidden@example.org", obj if len(obj) <= 600 else filler(200))
    return obj


def sanitize(path: Path) -> None:
    raw = path.read_text()
    if path.suffix == ".json":
        path.write_text(json.dumps(sanitize_json(json.loads(raw))))
    elif path.suffix in (".xml", ".rss"):
        path.write_text(sanitize_xml(raw))
    elif path.suffix in (".html", ".htm"):
        path.write_text(sanitize_html(raw))
    elif path.suffix == ".ics":
        path.write_text(re.sub(r"^(DESCRIPTION:).*?(?=^\S)", rf"\1{PLACEHOLDER}\r\n", raw, flags=re.M | re.S))
    print(f"sanitized {path} ({len(raw)} -> {path.stat().st_size} bytes)")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        sanitize(Path(arg))
