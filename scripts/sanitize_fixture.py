"""Sanitize saved pages before committing them as fixtures. The logic lives in openroster/ops/sanitize.py.

Usage: uv run python scripts/sanitize_fixture.py <file> [<file> ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openroster.ops.sanitize import sanitize  # noqa: E402

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        sanitize(Path(arg))
