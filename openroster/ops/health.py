"""Source health: turn data/health/state.json into problems, and keep one GitHub issue per failing source.

A problem is any of: the fetch failed, the source returned zero results after previously returning some, the
page structure changed (HTML sources), or the site now refuses us (robots.txt / known verdict). Nothing fails
silently: every problem opens or updates an issue titled "[health] <source id>". Issues close themselves after
the source has been healthy for two runs in a row.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from ..pipeline import store

HEALTHY_RUNS_TO_CLOSE = 2


def problems(state: dict[str, Any] | None = None) -> list[dict[str, str]]:
    state = state if state is not None else store.load_json(store.STATE, {})
    out: list[dict[str, str]] = []
    for sid, s in sorted(state.get("sources", {}).items()):
        if s.get("refused"):
            out.append({"source": sid, "kind": "refused", "detail": s.get("error") or "refused by policy"})
        elif not s.get("ok"):
            out.append({"source": sid, "kind": "fetch_error",
                        "detail": f"{s.get('error')} (failed {s.get('consecutive_failures', 1)} run(s) in a row)"})
        elif s.get("raw_count", 0) == 0 and s.get("last_nonzero", 0) > 0:
            out.append({"source": sid, "kind": "zero_results",
                        "detail": f"returns 0 items; it last returned {s.get('last_nonzero')}"})
        elif s.get("healthy_streak", 0) == 0 and s.get("prev_fingerprint") and s["fingerprint"] != s["prev_fingerprint"]:
            out.append({"source": sid, "kind": "structure_changed",
                        "detail": f"page structure fingerprint changed ({s['prev_fingerprint']} -> {s['fingerprint']})"})
    return out


def issue_body(p: dict[str, str]) -> str:
    hints = {
        "fetch_error": "The site may be down, or the URL moved. Check the source URL in config/sources/.",
        "zero_results": "The page may have been redesigned, or the event list is empty this season. "
        "If redesigned, update the selectors (run `openroster suggest-selectors <id>`).",
        "structure_changed": "The HTML changed. Results may be incomplete. Run `openroster suggest-selectors <id>` "
        "for rule-based selector suggestions, or let the AI repair job open a PR.",
        "refused": "robots.txt or a known verdict now forbids this source. It has been stopped automatically. "
        "Do not work around it; disable it in config or ask the site for a feed.",
    }
    return (
        f"**Source:** `{p['source']}`\n**Problem:** {p['kind']}\n**Detail:** {p['detail']}\n\n"
        f"{hints.get(p['kind'], '')}\n\n"
        f"_This issue is managed by the health check and closes after {HEALTHY_RUNS_TO_CLOSE} healthy runs._"
    )


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def sync_issues(dry_run: bool = False) -> dict[str, list[str]]:
    """Open/update an issue per problem; close issues for sources healthy for long enough. Uses the gh CLI."""
    probs = {p["source"]: p for p in problems()}
    state = store.load_json(store.STATE, {})
    open_issues = json.loads(_gh("issue", "list", "--label", "health", "--state", "open", "--limit", "200",
                                 "--json", "number,title")) if not dry_run else []
    by_source = {i["title"].removeprefix("[health] ").strip(): i["number"] for i in open_issues}
    done: dict[str, list[str]] = {"opened": [], "updated": [], "closed": []}
    for sid, p in probs.items():
        body = issue_body(p)
        if sid in by_source:
            if not dry_run:
                _gh("issue", "comment", str(by_source[sid]), "--body", body)
            done["updated"].append(sid)
        else:
            if not dry_run:
                _gh("issue", "create", "--title", f"[health] {sid}", "--label", "health", "--body", body)
            done["opened"].append(sid)
    for sid, number in by_source.items():
        streak = state.get("sources", {}).get(sid, {}).get("healthy_streak", 0)
        if sid not in probs and streak >= HEALTHY_RUNS_TO_CLOSE:
            if not dry_run:
                _gh("issue", "close", str(number), "--comment", f"Healthy for {streak} runs in a row; closing.")
            done["closed"].append(sid)
    return done
