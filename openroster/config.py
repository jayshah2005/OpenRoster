"""Loading and validating the YAML configuration in config/."""

from __future__ import annotations

import os
from functools import cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
# OPENROSTER_DATA points the pipeline at another data folder (previews, tests).
DATA = Path(os.environ.get("OPENROSTER_DATA") or ROOT / "data")
GEO = ROOT / "data" / "geo"

REPO_URL = "https://github.com/jayshah2005/OpenRoster"
# The contact address is public. It is read from the environment so it can be set before the alias exists.
CONTACT = os.environ.get("OPENROSTER_CONTACT", "")


def user_agent() -> str:
    contact = f"; {CONTACT}" if CONTACT else ""
    return f"OpenRosterBot/0.1 (+{REPO_URL}{contact})"


Verdict = Literal["allowed", "permission_required", "blocked", "link_only", "unknown"]


class KnownVerdict(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hosts: list[str]
    verdict: Verdict
    reason: str
    allow_paths: list[str] | None = None
    permission: dict[str, Any] | None = None

    def matches(self, host: str) -> bool:
        host = host.lower()
        return any(host == h or host.endswith("." + h) for h in self.hosts)


class Audit(BaseModel):
    model_config = ConfigDict(extra="allow")
    robots: str = "unknown"
    terms_url: str | None = None
    terms_forbid: bool | None = None
    verdict: Verdict = "unknown"
    checked: str | None = None
    notes: str | None = None


class Source(BaseModel):
    """One configured source. Adapter-specific options live in `options`."""

    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    adapter: str
    url: str
    owner: str
    enabled: bool = True
    reviewed: bool = False
    page_budget: int = 20
    timezone: str = "America/Toronto"
    default_type: str | None = None
    default_roles: list[str] = Field(default_factory=lambda: ["participant"])
    schools: list[str] = Field(default_factory=list)
    eligibility: list[str] | None = None
    tags: list[str] = Field(default_factory=list)
    location: dict[str, str] | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    audit: Audit = Field(default_factory=Audit)
    hand_tuned: bool = False          # the research-to-config generator never overwrites this entry
    notes: str | None = None

    @property
    def host(self) -> str:
        return urlsplit(self.url).hostname or ""

    @property
    def runnable(self) -> bool:
        """Runs only when enabled, signed off by the owner, and the latest audit still says allowed.
        A later audit that turns blocked (robots or terms changed) stops the source automatically."""
        return self.enabled and self.reviewed and latest_verdict(self.id, self.audit.verdict) == "allowed"


def latest_verdict(source_id: str, fallback: str = "unknown") -> str:
    import json

    f = DATA / "audit" / f"{source_id.replace(':', '__')}.json"
    if f.exists():
        return str(json.loads(f.read_text()).get("verdict", fallback))
    return fallback


def _load(path: Path) -> Any:
    with path.open() as f:
        return yaml.safe_load(f) or {}


@cache
def known_verdicts() -> list[KnownVerdict]:
    return [KnownVerdict(**v) for v in _load(CONFIG / "known_verdicts.yaml")["verdicts"]]


def known_verdict_for(url: str) -> KnownVerdict | None:
    host = urlsplit(url).hostname or ""
    # Most specific (longest) host pattern wins, so api.lu.ma beats lu.ma.
    best: tuple[int, KnownVerdict] | None = None
    for kv in known_verdicts():
        for h in kv.hosts:
            matched = host == h or host.endswith("." + h)
            if matched and (best is None or len(h) > best[0]):
                best = (len(h), kv)
    return best[1] if best else None


def load_sources(path: Path | None = None) -> list[Source]:
    files = [path] if path else sorted((CONFIG / "sources").glob("*.yaml"))
    out: list[Source] = []
    for f in files:
        out.extend(Source(**s) for s in (_load(f).get("sources") or []))
    ids = [s.id for s in out]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate source ids: {sorted(dupes)}")
    return out


def load_yaml(name: str) -> Any:
    return _load(CONFIG / name)
