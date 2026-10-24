#!/usr/bin/env python3
"""PreToolUse hook (Bash): enforce .claude/skills/commit-convention/SKILL.md.

Blocks `git commit` with a subject that breaks the convention and `git checkout -b` / `git switch -c` /
`git branch <name>` / `git worktree add -b` with a branch name that breaks it. The scope allowlist is read from the
skill's table, so the skill stays the single source of truth. Exit 2 blocks the command and shows the reason to
Claude; anything else lets it run.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "commit-convention" / "SKILL.md"
TYPES = ("feat", "fix", "refactor", "chore")
EXEMPT_BRANCH_PREFIXES = ("bot/", "ai/")


def scopes() -> set[str]:
    text = SKILL.read_text() if SKILL.exists() else ""
    section = text.split("## Scope allowlist", 1)[-1].split("\n## ", 1)[0]
    return {m.group(1) for m in re.finditer(r"^\|\s*([a-z][a-z0-9-]*)\s*\|", section, re.M)} - {"scope"}


def check_subject(subject: str, allowed: set[str]) -> str | None:
    m = re.fullmatch(r"([a-z]+)((?:/[a-z0-9-]+)*(?:\+[a-z0-9-]+(?:/[a-z0-9-]+)*)*)?: (.+)", subject)
    if not m:
        return "subject must look like `type[/scope[/subscope]][+scope]: summary`"
    typ, scope_part, summary = m.group(1), m.group(2) or "", m.group(3)
    if typ not in TYPES:
        return f"type `{typ}` is not allowed; use one of {', '.join(TYPES)}"
    for combined in filter(None, scope_part.lstrip("/").split("+")):
        top = combined.split("/")[0]
        if top not in allowed:
            return f"scope `{top}` is not in the allowlist ({', '.join(sorted(allowed))}); ask the user before adding one"
    if summary[:1] != summary[:1].lower():
        return "summary must start with a lowercase word"
    if summary.endswith("."):
        return "summary must not end with a period"
    if len(subject) > 60:
        return f"subject is {len(subject)} characters; keep it under about 50 (hard limit 60)"
    return None


def check_branch(name: str, allowed: set[str]) -> str | None:
    if name.startswith(EXEMPT_BRANCH_PREFIXES) or name in ("main", "master"):
        return None
    m = re.fullmatch(r"([a-z]+)/([a-z0-9]+)(-[a-z0-9-]+)?", name)
    if not m:
        return "branch must look like `type/scope[-short-slug]`, e.g. `feat/adapters-rss`"
    if m.group(1) not in TYPES:
        return f"branch type `{m.group(1)}` is not allowed; use one of {', '.join(TYPES)}"
    if m.group(2) not in allowed:
        return f"branch scope `{m.group(2)}` is not in the allowlist; ask the user before adding one"
    return None


def commit_subject(segment: str, tokens: list[str], full: str) -> str | None | bool:
    """The commit's subject line; False when the commit reuses a message; None when it can't be found."""
    if "--no-edit" in tokens or any(t.startswith(("--fixup", "--squash", "-C", "--reuse-message")) for t in tokens):
        return False
    heredoc = re.search(r"<<-?\s*['\"]?(\w+)['\"]?\s*\n(.*?)\n\s*\1\b", full, re.S)
    if heredoc and ("-F" in tokens or any("<<" in t for t in tokens)):
        return heredoc.group(2).strip().splitlines()[0].strip() if heredoc.group(2).strip() else ""
    for i, t in enumerate(tokens):
        if t in ("-m", "--message") and i + 1 < len(tokens):
            return tokens[i + 1].strip().splitlines()[0].strip() if tokens[i + 1].strip() else ""
        if t.startswith("--message="):
            return t.split("=", 1)[1].strip().splitlines()[0]
        if t.startswith("-m") and len(t) > 2 and not t.startswith("--"):
            return t[2:].strip().splitlines()[0]
        if t in ("-F", "--file") and i + 1 < len(tokens) and tokens[i + 1] != "-":
            p = Path(tokens[i + 1])
            if p.exists():
                lines = [ln for ln in p.read_text().splitlines() if not ln.startswith("#")]
                return lines[0].strip() if lines else ""
    return None


def segments(command: str) -> list[str]:
    # Split on shell operators so `git add x && git commit -m ...` is checked; heredoc bodies stay attached.
    return [s for s in re.split(r"\s*(?:&&|\|\||;|\n(?=\s*git\b))\s*", command) if re.search(r"\bgit\b", s)]


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not re.search(r"\bgit\b", command):
        return 0
    allowed = scopes()
    problems: list[str] = []
    for seg in segments(command):
        tokens = tokenize(seg)
        try:
            g = tokens.index("git")
        except ValueError:
            continue
        # Skip git's global options (before the subcommand), e.g. `git -C dir -c k=v commit ...`.
        rest = tokens[g + 1:]
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
        if not rest:
            continue
        sub, args = rest[0], rest[1:]
        if sub == "commit":
            subject = commit_subject(seg, args, command)
            if subject is False:
                continue
            if subject is None:
                problems.append("could not read the commit message; use `git commit -m \"...\"` or `-F <file>`")
            elif (err := check_subject(subject, allowed)):
                problems.append(f"commit `{subject}`: {err}")
        elif sub in ("checkout", "switch") or (sub == "worktree" and args[:1] == ["add"]):
            for i, t in enumerate(args):
                if t in ("-b", "-B", "-c", "-C", "--create", "--force-create") and i + 1 < len(args):
                    if (err := check_branch(args[i + 1], allowed)):
                        problems.append(f"branch `{args[i + 1]}`: {err}")
        elif sub == "branch":
            if any(t.startswith("-") for t in args) or not args:
                continue  # listing, deleting, renaming flags, --show-current, etc.
            if (err := check_branch(args[0], allowed)):
                problems.append(f"branch `{args[0]}`: {err}")
    if problems:
        print("Blocked by the commit convention (.claude/skills/commit-convention/SKILL.md):\n- "
              + "\n- ".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
