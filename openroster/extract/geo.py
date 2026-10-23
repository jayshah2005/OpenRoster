"""Offline place lookup (GeoNames, CC BY) and distances to campuses. No geocoding API is called."""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from functools import cache

from ..config import GEO, load_yaml

REGION_NAMES = {
    "ontario": "CA-ON", "quebec": "CA-QC", "québec": "CA-QC", "british columbia": "CA-BC", "alberta": "CA-AB",
    "manitoba": "CA-MB", "saskatchewan": "CA-SK", "nova scotia": "CA-NS", "new brunswick": "CA-NB",
    "newfoundland": "CA-NL", "prince edward island": "CA-PE",
}
REGION_ABBR = re.compile(r",\s*(ON|QC|BC|AB|MB|SK|NS|NB|NL|PE)\b")


@dataclass(frozen=True)
class Place:
    name: str
    region: str
    country: str
    lat: float
    lon: float
    pop: int


@cache
def _places() -> dict[str, list[Place]]:
    by_name: dict[str, list[Place]] = {}
    with (GEO / "cities.tsv").open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            p = Place(row["name"], row["region"], row["country"], float(row["lat"]), float(row["lon"]),
                      int(row["pop"] or 0))
            by_name.setdefault(_norm(p.name), []).append(p)
    for k in by_name:
        by_name[k].sort(key=lambda p: (p.country != "CA", p.region != "CA-ON", -p.pop))
    return by_name


@cache
def _city_regex() -> re.Pattern[str]:
    """Canadian place names (pop >= 5000), longest first, for finding a city mentioned in free text."""
    names = sorted({p.name for ps in _places().values() for p in ps if p.country == "CA"}, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")


def _norm(s: str) -> str:
    s = re.sub(r"\b(?:saint|st\.?)\s+", "st. ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def lookup(city: str | None, region: str | None = None, country: str | None = None) -> Place | None:
    if not city:
        return None
    cands = _places().get(_norm(city), [])
    if region:
        cands = [p for p in cands if p.region == region] or cands
    if country:
        cands = [p for p in cands if p.country == country] or cands
    return cands[0] if cands else None


def find_place_in_text(text: str) -> Place | None:
    """The first Canadian city named in text, preferring one followed by a province (", ON")."""
    if not text:
        return None
    for m in _city_regex().finditer(text):
        tail = text[m.end() : m.end() + 6]
        abbr = REGION_ABBR.match(tail)
        region = f"CA-{abbr.group(1)}" if abbr else None
        p = lookup(m.group(1), region, "CA")
        if p:
            return p
    return None


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class Campus:
    school_id: str
    school_name: str
    campus: str
    city: str | None
    lat: float
    lon: float


@cache
def campuses() -> tuple[Campus, ...]:
    out: list[Campus] = []
    for s in load_yaml("schools.yaml").get("schools", []):
        for c in s.get("campuses", []):
            if c.get("lat") is not None and c.get("lon") is not None:
                out.append(Campus(s["id"], s["name"], c.get("name", ""), c.get("city"), float(c["lat"]), float(c["lon"])))
    return tuple(out)


@cache
def _school_names() -> list[tuple[re.Pattern[str], Campus]]:
    """Regexes for school names and aliases (from schools.yaml) -> their first campus."""
    out: list[tuple[re.Pattern[str], Campus]] = []
    by_id = {c.school_id: c for c in reversed(campuses())}  # first campus wins
    for s in load_yaml("schools.yaml").get("schools", []):
        c = by_id.get(s["id"])
        if not c:
            continue
        for name in [s["name"], *s.get("aliases", [])]:
            out.append((re.compile(r"\b" + re.escape(name) + r"\b", re.I), c))
    out.sort(key=lambda t: len(t[0].pattern), reverse=True)  # "McMaster University MBA" style: longest first
    return out


def find_school_in_text(text: str) -> Campus | None:
    for rx, campus in _school_names():
        if rx.search(text or ""):
            return campus
    return None


def near_schools(lat: float, lon: float, max_km: float = 100.0) -> list[tuple[str, float]]:
    best: dict[str, float] = {}
    for c in campuses():
        d = km(lat, lon, c.lat, c.lon)
        if d <= max_km and d < best.get(c.school_id, 1e9):
            best[c.school_id] = d
    return sorted(((k, round(v, 1)) for k, v in best.items()), key=lambda t: t[1])
