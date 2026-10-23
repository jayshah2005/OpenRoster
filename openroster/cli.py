"""openroster command line."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import ROOT


def cmd_audit(a: argparse.Namespace) -> int:
    from .audit.core import audit_url, format_result, result_dict
    from .audit.report import audit_all, write_report

    if a.all:
        results = audit_all(only=set(a.only) if a.only else None)
        write_report()
        for sid, r in results.items():
            print(f"{r.verdict:20} {sid}")
        print(f"\nWrote reports/source-audit.md ({len(results)} audited)")
        return 0
    if not a.url:
        print("give a URL or --all", file=sys.stderr)
        return 2
    for url in a.url:
        r = audit_url(url)
        print(json.dumps(result_dict(r), indent=2) if a.json else format_result(r))
        print()
    return 0


def cmd_scrape(a: argparse.Namespace) -> int:
    from .pipeline.run import run

    rep = run(only=set(a.only) if a.only else None, include_hackathons=not a.no_hackathons)
    failing = {k: v for k, v in rep.health.items() if not v.ok}
    print(f"sources run: {len(rep.health)}  failing: {len(failing)}  skipped (not runnable): {len(rep.skipped)}")
    print(f"new: {len(rep.new)}  updated: {rep.updated}  archived: {len(rep.archived)}  "
          f"review items: {len(rep.review)}  flagged missing: {len(rep.flagged_missing)}")
    for k, v in failing.items():
        print(f"  FAIL {k}: {v.error}")
    return 0


def cmd_validate(a: argparse.Namespace) -> int:
    from .validate import validate_all

    errors = validate_all()
    for e in errors:
        print(e)
    print(f"{'FAILED' if errors else 'OK'}: {len(errors)} problem(s)")
    return 1 if errors else 0


def cmd_schema(a: argparse.Namespace) -> int:
    from .model import export_json_schema

    text = json.dumps(export_json_schema(), indent=2) + "\n"
    path = ROOT / "schema" / "opportunity.schema.json"
    if a.check:
        if not path.exists() or path.read_text() != text:
            print("schema/opportunity.schema.json is out of date: run `openroster schema`")
            return 1
        return 0
    path.write_text(text)
    return 0


def cmd_health(a: argparse.Namespace) -> int:
    from .ops.health import problems, sync_issues

    probs = problems()
    print(json.dumps(probs, indent=2))
    if a.sync:
        print(json.dumps(sync_issues(dry_run=a.dry_run), indent=2))
    return 0


def cmd_review(a: argparse.Namespace) -> int:
    from .ops.review import write_review

    path = write_review()
    print(f"wrote {path}")
    return 0


def cmd_submission(a: argparse.Namespace) -> int:
    from .ops.submission import as_json, comment_for, parse_issue

    body = sys.stdin.read() if a.body == "-" else Path(a.body).read_text()
    result = parse_issue(body, kind=a.kind, issue_number=a.issue, write=a.write)
    if a.comment_file:
        Path(a.comment_file).write_text(comment_for(result))
    print(as_json(result))
    return 0 if result["ok"] else 1


def cmd_propose(a: argparse.Namespace) -> int:
    from .ops.approvals import propose

    flipped, body = propose()
    print(f"proposed {len(flipped)} source(s) for sign-off; PR body in {body.relative_to(ROOT)}")
    return 0


def cmd_suggest(a: argparse.Namespace) -> int:
    from .config import load_sources
    from .fetch import Fetcher
    from .ops.selectors import suggest

    src = next((s for s in load_sources() if s.id == a.source), None)
    if src is None:
        print(f"unknown source {a.source}", file=sys.stderr)
        return 2
    html = Path(a.html).read_text() if a.html else Fetcher().get(src.url, source_id=src.id).text
    for s in suggest(html):
        print(f"item: {s.item!r}  title: {s.title!r}  ({s.count} blocks, {s.dated} with dates)")
        print(f"   e.g. {s.sample}")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="openroster")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("audit", help="audit URLs, or every configured source with --all")
    s.add_argument("url", nargs="*")
    s.add_argument("--all", action="store_true")
    s.add_argument("--only", nargs="*")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("scrape", help="run all runnable sources and update data/")
    s.add_argument("--only", nargs="*")
    s.add_argument("--no-hackathons", action="store_true")
    s.set_defaults(fn=cmd_scrape)

    s = sub.add_parser("validate", help="validate data/ against the schema and the no-personal-data rule")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("schema", help="export the JSON Schema")
    s.add_argument("--check", action="store_true")
    s.set_defaults(fn=cmd_schema)

    s = sub.add_parser("health", help="print source health problems; --sync opens/updates/closes GitHub issues")
    s.add_argument("--sync", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_health)

    s = sub.add_parser("propose-approvals", help="set reviewed: true on audited-allowed sources (for the sign-off PR)")
    s.set_defaults(fn=cmd_propose)

    s = sub.add_parser("suggest-selectors", help="rule-based selector suggestions for an HTML source")
    s.add_argument("source")
    s.add_argument("--html", help="read a saved page instead of fetching")
    s.set_defaults(fn=cmd_suggest)

    s = sub.add_parser("review", help="write the review file for the daily review PR")
    s.set_defaults(fn=cmd_review)

    s = sub.add_parser("submission", help="parse and validate an issue-form body")
    s.add_argument("--body", default="-")
    s.add_argument("--kind", default="submit", choices=["submit", "correct", "takedown", "permission"])
    s.add_argument("--issue", type=int, default=0)
    s.add_argument("--write", action="store_true", help="apply the change to config/ or data/")
    s.add_argument("--comment-file", help="write a reply for the issue to this file")
    s.set_defaults(fn=cmd_submission)

    a = p.parse_args(argv)
    return int(a.fn(a))


if __name__ == "__main__":
    sys.exit(main())
