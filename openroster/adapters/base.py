"""What adapters produce: raw candidates with evidence. The pipeline turns candidates into Opportunity records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..config import Source
from ..fetch import Fetcher


@dataclass
class RoleCandidate:
    role: str
    opens: datetime | None = None
    closes: datetime | None = None
    status: str = "unknown"
    url: str | None = None
    evidence: str | None = None


@dataclass
class Candidate:
    source_id: str
    adapter: str                      # an Obtained value
    url: str                          # the page a person should open
    title: str
    start: datetime | None = None
    end: datetime | None = None
    all_day: bool = False
    timezone: str | None = None
    uid: str | None = None            # stable id from the source (ICS UID, API id)
    organizer: str | None = None
    type: str | None = None
    roles: list[RoleCandidate] = field(default_factory=list)
    mode: str | None = None
    venue: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    lat: float | None = None
    lon: float | None = None
    registration_url: str | None = None
    cost: str | None = None
    tags: list[str] = field(default_factory=list)
    eligibility: list[str] | None = None
    schools: list[str] | None = None
    cancelled: bool = False
    series_id: str | None = None
    summary: str | None = None        # hand-written only (manual / submissions); otherwise rule-built
    # Text used only for rule-based classification; never stored or published.
    text: str = ""
    date_evidence: str | None = None
    date_confidence: str = "explicit"   # explicit | inferred_year | structured | none
    review_reasons: list[str] = field(default_factory=list)
    ai_suggested: list[str] = field(default_factory=list)  # fields an AI proposed and a person accepted


@dataclass
class AdapterResult:
    candidates: list[Candidate] = field(default_factory=list)
    pages: int = 0
    errors: list[str] = field(default_factory=list)
    # Structure fingerprint for health checks (HTML adapters); None for feeds.
    fingerprint: str | None = None
    raw_count: int = 0                # items seen before relevance filtering


class Adapter:
    name: str = ""

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:  # pragma: no cover - interface
        raise NotImplementedError
