"""Canonical opportunity schema. The JSON Schema in schema/ is exported from these models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class OppType(StrEnum):
    hackathon = "hackathon"
    info_session = "info_session"
    tech_talk = "tech_talk"
    career_fair = "career_fair"
    networking = "networking"
    workshop = "workshop"
    conference = "conference"
    case_competition = "case_competition"
    early_career_program = "early_career_program"
    other = "other"


class Role(StrEnum):
    participant = "participant"
    volunteer = "volunteer"
    mentor = "mentor"
    judge = "judge"
    organizer_team = "organizer_team"
    workshop_lead = "workshop_lead"


class RoleStatus(StrEnum):
    upcoming = "upcoming"
    open = "open"
    closed = "closed"
    unknown = "unknown"


class Mode(StrEnum):
    in_person = "in_person"
    online = "online"
    hybrid = "hybrid"
    unknown = "unknown"


class Eligibility(StrEnum):
    open_to_all = "open_to_all"
    school_only = "school_only"
    high_school = "high_school"
    undergrad = "undergrad"
    grad = "grad"
    unknown = "unknown"


class RegRoute(StrEnum):
    public_link = "public_link"
    school_portal_login = "school_portal_login"
    form = "form"
    email = "email"
    unknown = "unknown"


class CostKind(StrEnum):
    free = "free"
    paid = "paid"
    unknown = "unknown"


class Status(StrEnum):
    scheduled = "scheduled"
    moved = "moved"
    cancelled = "cancelled"
    needs_review = "needs_review"
    past = "past"


class Obtained(StrEnum):
    ics = "ics"
    rss = "rss"
    tribe = "tribe"
    localist = "localist"
    jsonld = "jsonld"
    sitemap = "sitemap"
    html = "html"
    headless = "headless"
    api = "api"
    hackathon_site = "hackathon_site"
    submission = "submission"
    manual = "manual"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class RoleWindow(Strict):
    role: Role
    opens: AwareDatetime | None = None
    closes: AwareDatetime | None = None
    status: RoleStatus = RoleStatus.unknown
    url: str | None = None
    evidence: str | None = Field(default=None, max_length=300)


class Location(Strict):
    venue_name: str | None = None
    city: str | None = None
    region: str | None = Field(default=None, pattern=r"^[A-Z]{2}-[A-Z0-9]{1,3}$")
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")


class Geo(Strict):
    lat: float
    lon: float
    source: str = "gazetteer"


class NearSchool(Strict):
    school_id: str
    km: float


class Registration(Strict):
    route: RegRoute = RegRoute.unknown
    url: str | None = None


class Cost(Strict):
    kind: CostKind = CostKind.unknown
    note: str | None = None


class TravelSupport(Strict):
    stated: bool = False
    note: str | None = None


class SourceRef(Strict):
    url: str
    adapter: Obtained
    source_id: str
    fetched_at: AwareDatetime


class HistoryEntry(Strict):
    at: AwareDatetime
    field: str
    old: str | None
    new: str | None


class Evidence(Strict):
    text: str = Field(max_length=500)
    url: str


class Review(Strict):
    reasons: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class Opportunity(Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,120}$")
    type: OppType
    title: str = Field(min_length=2, max_length=200)
    organizer: str = Field(min_length=1, max_length=120)
    roles: list[RoleWindow] = Field(min_length=1)
    start: AwareDatetime
    end: AwareDatetime | None = None
    timezone: str
    all_day: bool = False
    series_id: str | None = None
    mode: Mode = Mode.unknown
    location: Location = Field(default_factory=Location)
    geo: Geo | None = None
    near_schools: list[NearSchool] = Field(default_factory=list)
    schools: list[str] = Field(default_factory=lambda: ["open_to_all"])
    eligibility: list[Eligibility] = Field(default_factory=lambda: [Eligibility.unknown])
    registration: Registration = Field(default_factory=Registration)
    cost: Cost = Field(default_factory=Cost)
    travel_support: TravelSupport = Field(default_factory=TravelSupport)
    tags: list[str] = Field(default_factory=list)
    summary: str = Field(default="", max_length=200)
    sources: list[SourceRef] = Field(min_length=1)
    obtained_via: list[Obtained] = Field(min_length=1)
    first_seen: AwareDatetime
    last_seen: AwareDatetime
    last_verified: AwareDatetime
    status: Status = Status.scheduled
    history: list[HistoryEntry] = Field(default_factory=list)
    review: Review | None = None
    ai_suggested: list[str] = Field(default_factory=list, description="Field names filled by an AI suggestion")

    @field_validator("timezone")
    @classmethod
    def _valid_tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(f"unknown IANA time zone: {v}") from e
        return v

    @model_validator(mode="after")
    def _check_order(self) -> Opportunity:
        if self.end and self.end < self.start:
            raise ValueError("end is before start")
        for r in self.roles:
            if r.opens and r.closes and r.closes < r.opens:
                raise ValueError(f"role {r.role}: closes before opens")
        return self

    def sort_key(self) -> tuple[datetime, datetime]:
        """Soonest open deadline first, then start."""
        deadlines = [r.closes for r in self.roles if r.closes and r.status != RoleStatus.closed]
        return (min(deadlines) if deadlines else self.start, self.start)


def export_json_schema() -> dict:
    schema = Opportunity.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://github.com/jayshah2005/OpenRoster/schema/opportunity.schema.json"
    return schema
