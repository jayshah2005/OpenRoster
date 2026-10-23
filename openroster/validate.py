"""Data validation for CI: JSON Schema, cross-field rules, and the no-personal-data rule."""

from __future__ import annotations

import json
import re

from jsonschema import Draft202012Validator

from .config import DATA, ROOT, load_sources, load_yaml

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)")
HANDLE = re.compile(r"(?<![\w/.])@[A-Za-z0-9_]{3,}\b")
# Fields that hold URLs; a URL may contain "@" (calendar ids) without being personal data.
URL_KEYS = {"url", "landing_url"}


def _strings(obj: object, path: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += _strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        out.append((path, obj))
    return out


def pii_problems(doc: dict, name: str) -> list[str]:
    errs = []
    for path, s in _strings(doc):
        last = re.sub(r"\[\d+\]", "", path).split(".")[-1]
        if last in URL_KEYS or s.startswith(("http://", "https://", "mailto:")):
            continue
        if EMAIL.search(s):
            errs.append(f"{name}: email address in {path}")
        if PHONE.search(s):
            errs.append(f"{name}: phone number in {path}")
        if HANDLE.search(s) and last not in ("evidence", "text"):
            errs.append(f"{name}: social handle in {path}")
    return errs


def validate_all() -> list[str]:
    errors: list[str] = []
    schema = json.loads((ROOT / "schema" / "opportunity.schema.json").read_text())
    validator = Draft202012Validator(schema)
    files = sorted((DATA / "records").glob("*.json")) + sorted((DATA / "archive").glob("*/*.json"))
    ids: dict[str, str] = {}
    for f in files:
        try:
            doc = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: invalid JSON: {e}")
            continue
        for err in validator.iter_errors(doc):
            errors.append(f"{f.name}: {'/'.join(map(str, err.path))}: {err.message}")
        if doc.get("id") != f.stem:
            errors.append(f"{f.name}: id {doc.get('id')!r} does not match file name")
        if doc.get("id") in ids:
            errors.append(f"{f.name}: duplicate id also in {ids[doc['id']]}")
        ids[doc.get("id", "")] = f.name
        errors += pii_problems(doc, f.name)
    # Config sanity
    try:
        sources = load_sources()
    except Exception as e:
        errors.append(f"config/sources: {e}")
        sources = []
    for s in sources:
        if s.adapter not in {"ics", "tribe", "localist", "jsonld", "sitemap", "html", "headless", "hackclub", "rss", "json"}:
            errors.append(f"source {s.id}: unknown adapter {s.adapter}")
        if s.enabled and s.adapter in ("html", "headless") and "item" not in s.options:
            errors.append(f"source {s.id}: html adapters need options.item")
    seen = set()
    for h in load_yaml("hackathons.yaml").get("hackathons") or []:
        if h.get("id") in seen:
            errors.append(f"hackathon {h.get('id')}: duplicate id")
        seen.add(h.get("id"))
    return errors
