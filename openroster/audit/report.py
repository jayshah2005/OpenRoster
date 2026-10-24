"""Audit every configured source and hackathon, store results in data/audit/, and write reports/source-audit.md."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ..config import DATA, ROOT, known_verdicts, load_sources
from ..fetch import Fetcher
from ..hackathons import load_hackathons
from ..parallel import by_host
from ..pipeline.store import dump, write_if_changed
from .core import AuditResult, audit_url, result_dict

AUDIT_DIR = DATA / "audit"
REPORT = ROOT / "reports" / "source-audit.md"


def audit_path(sid: str):
    return AUDIT_DIR / f"{sid.replace(':', '__')}.json"


def targets() -> list[tuple[str, str, str, bool]]:
    """(id, name, url, reviewed) for every source and hackathon."""
    out = [(s.id, s.name, s.url, s.reviewed) for s in load_sources()]
    out += [(f"hackathon:{h.id}", h.name, h.url, h.reviewed) for h in load_hackathons()]
    return out


def safe_audit(url: str, fetcher: Fetcher) -> AuditResult:
    """One site's unexpected error is recorded on that site instead of stopping the whole audit."""
    try:
        return audit_url(url, fetcher)
    except Exception as e:  # noqa: BLE001 - deliberately broad: report and move on
        r = AuditResult(url=url, checked=datetime.now(UTC).isoformat(), verdict="unknown")
        r.reasons.append(f"audit error: {type(e).__name__}: {e}"[:300])
        return r


def audit_all(fetcher: Fetcher | None = None, only: set[str] | None = None) -> dict[str, AuditResult]:
    """Audit every source and hackathon. Different sites are audited in parallel (one worker per host, see
    parallel.py); pass a `fetcher` to run sequentially with it instead (tests)."""
    todo = [(sid, url) for sid, _name, url, _rev in targets() if not only or sid in only]
    if fetcher is not None:
        pairs = [((sid, url), audit_url(url, fetcher)) for sid, url in todo]
    else:
        pairs = by_host(todo, url_of=lambda t: t[1], work=lambda t, f: safe_audit(t[1], f))
    results: dict[str, AuditResult] = {}
    for (sid, _url), r in pairs:
        results[sid] = r
        prev = json.loads(audit_path(sid).read_text()) if audit_path(sid).exists() else None
        d = result_dict(r)
        # Do not churn the file when only the timestamp changed.
        if prev and {k: v for k, v in prev.items() if k != "checked"} == {k: v for k, v in d.items() if k != "checked"}:
            continue
        write_if_changed(audit_path(sid), dump(d))
    return results


def load_results() -> dict[str, dict]:
    return {
        sid: json.loads(audit_path(sid).read_text())
        for sid, *_ in targets()
        if audit_path(sid).exists()
    }


def write_report() -> str:
    rows = []
    stored = load_results()
    counts: dict[str, int] = {}
    for sid, name, url, reviewed in targets():
        a = stored.get(sid)
        verdict = a["verdict"] if a else "not audited"
        counts[verdict] = counts.get(verdict, 0) + 1
        terms = a.get("terms_url") if a else None
        flags = []
        if a and a.get("terms_forbid_automated"):
            flags.append("terms: automated access")
        if a and a.get("terms_forbid_republish"):
            flags.append("terms: republishing")
        rows.append(
            f"| `{sid}` | [{name}]({url}) | **{verdict}** | {a['robots'] if a else '-'} | "
            f"{f'[terms]({terms})' if terms else '-'} | {', '.join(flags) or '-'} | "
            f"{a['platform'] if a else '-'} | {'yes' if reviewed else 'no'} | {(a or {}).get('checked', '-')[:10]} |"
        )
    lines = [
        "# Source audit report",
        "",
        f"Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC by `openroster audit --all`. "
        "A source runs only when its verdict is **allowed** and the owner set `reviewed: true`.",
        "",
        "Summary: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())),
        "",
        "## Known verdicts (always enforced in code)",
        "",
        "| Hosts | Verdict | Reason |",
        "|---|---|---|",
    ]
    lines += [f"| {', '.join(k.hosts)} | **{k.verdict}** | {k.reason} |" for k in known_verdicts()]
    lines += [
        "",
        "## Configured sources and hackathons",
        "",
        "| ID | Source | Verdict | robots.txt | Terms | Terms flags | Platform | Reviewed | Checked |",
        "|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "Terms quotes for each source are in `data/audit/<id>.json` (`terms_quotes`).",
        "",
    ]
    text = "\n".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    # The timestamp alone must not create a commit.
    if REPORT.exists() and REPORT.read_text().split("\n", 3)[3:] == text.split("\n", 3)[3:]:
        return text
    REPORT.write_text(text)
    return text
