"""The commit-convention hook (.claude/hooks/check_git_convention.py) blocks bad commits and branch names."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "check_git_convention.py"


def run(command: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_input": {"command": command}}),
                       capture_output=True, text=True)
    return p.returncode, p.stderr


GOOD_HEREDOC = """git add a && git commit -q -F - <<'EOF'
chore/docs: add architecture guide and license

Co-Authored-By: someone
EOF"""

TWO_COMMITS_SECOND_BAD = """git add a && git commit -q -F - <<'EOF'
chore/docs: add architecture guide and license
EOF
git add b && git commit -q -F - <<'EOF'
Bad second message.
EOF"""

SCRIPT_THEN_COMMIT = """python3 - <<'EOF'
print("not a commit message")
EOF
git commit -m "fix/ci: wait for passing checks"
"""

FIXTURE_WITH_GIT_LINES = """cat > /tmp/case.txt <<'OUTER'
git commit -m "Not a real commit"
git switch -c not-a-real-branch
OUTER
ls"""


@pytest.mark.parametrize("cmd", [
    'git commit -m "feat/adapters/rss: add engage rss adapter"',
    'git add web/app && git commit -m "refactor/web/filters: share filter logic"',
    GOOD_HEREDOC,
    SCRIPT_THEN_COMMIT,
    FIXTURE_WITH_GIT_LINES,
    "git commit --amend --no-edit",
    "git checkout -b feat/adapters-rss",
    "git branch -D old-branch",
    "git -C web status",
    "git push -u origin main",
    "ls -la",
])
def test_allowed(cmd):
    code, err = run(cmd)
    assert code == 0, err


@pytest.mark.parametrize(("cmd", "why"), [
    ('git commit -m "OpenRoster: everything"', "subject must look like"),
    ('git commit -m "docs: update readme"', "type `docs` is not allowed"),
    ('git commit -m "feat/frontend: add thing"', "scope `frontend` is not in the allowlist"),
    ('git commit -m "fix/extract: Stop reading at."', "lowercase"),
    ('git commit -m "chore/docs: add architecture guide, license and refresh readme too"', "characters"),
    (TWO_COMMITS_SECOND_BAD, "Bad second message."),
    ("git switch -c my-branch", "branch must look like"),
    ("git commit", "could not read the commit message"),
])
def test_blocked(cmd, why):
    code, err = run(cmd)
    assert code == 2 and why in err, err
