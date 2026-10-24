"""Source sign-off: propose `reviewed: true` for every audited-as-allowed source, as one pull request.

Merging that PR is the owner's sign-off (the spec requires a person to approve each source). The PR body lists
each source with its robots.txt result, terms URL and the quoted terms clauses, so the review takes seconds;
the owner can delete any line from the diff before merging to keep a source off.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from ..audit.report import load_results
from ..config import CONFIG, ROOT

BODY = ROOT / "reports" / "source-review.md"


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # never re-wrap lines, so the PR diff shows only the real changes
    y.indent(mapping=2, sequence=2, offset=0)
    return y


def propose() -> tuple[list[str], Path]:
    audits = load_results()
    y = _yaml()
    flipped: list[str] = []
    rows: list[str] = []
    files = sorted((CONFIG / "sources").glob("*.yaml")) + [CONFIG / "hackathons.yaml"]
    for path in files:
        doc = y.load(path.read_text())
        key = "hackathons" if path.name == "hackathons.yaml" else "sources"
        changed = False
        for entry in doc.get(key) or []:
            sid = f"hackathon:{entry['id']}" if key == "hackathons" else entry["id"]
            a = audits.get(sid)
            # Disabled sources are included: sign-off is what lets `autoselect` fetch an HTML page once to find its
            # selectors, and a source only runs once it is also enabled.
            if entry.get("reviewed") or not a or a.get("verdict") != "allowed":
                continue
            entry["reviewed"] = True
            changed = True
            flipped.append(sid)
            quotes = "<br>".join(f"“{q}”" for q in a.get("terms_quotes", [])) or "no relevant clause found"
            terms = f"[terms]({a['terms_url']})" if a.get("terms_url") else "no terms page found"
            rows.append(f"| `{sid}` | [{entry.get('name', sid)}]({entry['url']}) | {a.get('robots')} | {terms} | "
                        f"{a.get('platform')} | {quotes} |")
        if changed:
            with path.open("w") as fh:
                y.dump(doc, fh)
    lines = [
        "## Source review",
        "",
        f"This PR marks **{len(flipped)}** audited sources as reviewed. **Merging it is your sign-off** that each "
        "one may be fetched. To keep a source off, remove its `reviewed: true` line from the diff before merging.",
        "",
        "Every source below passed the automatic audit: robots.txt allows the path, no terms clause forbidding "
        "automated access was found, and it is not on the blocked list. Clauses that restrict republishing are "
        "quoted; OpenRoster stores facts and links only.",
        "",
        "| ID | Source | robots.txt | Terms | Platform | Relevant terms clauses |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
    ]
    BODY.parent.mkdir(parents=True, exist_ok=True)
    BODY.write_text("\n".join(lines))
    return flipped, BODY
