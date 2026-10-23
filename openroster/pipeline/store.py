"""Git-as-database: one JSON file per record. Writes are stable (sorted keys) so unchanged data makes no diff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import DATA
from ..model import Opportunity

RECORDS = DATA / "records"
ARCHIVE = DATA / "archive"
REVIEW = DATA / "review"
STATE = DATA / "health" / "state.json"
KEYS = DATA / "keys.json"
ALIASES = DATA / "aliases.json"
TAKEDOWNS = DATA / "takedowns.json"


def dump(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text() == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def record_json(o: Opportunity) -> str:
    return dump(o.model_dump(mode="json", exclude_none=False))


def load_records(folder: Path | None = None) -> dict[str, Opportunity]:
    out: dict[str, Opportunity] = {}
    for f in sorted((folder or RECORDS).glob("*.json")):
        o = Opportunity.model_validate_json(f.read_text())
        out[o.id] = o
    return out


def load_archive() -> dict[str, Opportunity]:
    out: dict[str, Opportunity] = {}
    for f in sorted(ARCHIVE.glob("*/*.json")):
        o = Opportunity.model_validate_json(f.read_text())
        out[o.id] = o
    return out


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        return json.loads(path.read_text())
    return default


def takedowns() -> dict[str, list[str]]:
    """{"ids": [...], "urls": [...], "hosts": [...]} that must never be republished."""
    d = load_json(TAKEDOWNS, {})
    return {"ids": d.get("ids", []), "urls": d.get("urls", []), "hosts": d.get("hosts", [])}
