// Build-time data. The JSON modules are produced by scripts/gen-data.mjs from ../data and ../config,
// so the site never reads the filesystem at request time.
import archiveJson from "@/generated/archive.json";
import alsoUsefulJson from "@/generated/also-useful.json";
import indexJson from "@/generated/index.json";
import metaJson from "@/generated/meta.json";
import programsJson from "@/generated/programs.json";
import recordsJson from "@/generated/records.json";
import schoolsJson from "@/generated/schools.json";
import type { Entry, Link, Opportunity, Program, School } from "./types";

const records = recordsJson as unknown as Opportunity[];
const archive = archiveJson as unknown as Opportunity[];

export const meta = metaJson as { built: string; count: number };
export const entries = indexJson as unknown as Entry[];
export const schools = schoolsJson as School[];
export const schoolById = new Map(schools.map((s) => [s.id, s]));
export const alsoUseful = alsoUsefulJson as Link[];
/** Recurring early-career programs from config/programs.yaml (hand-curated). */
export const programs = programsJson as Program[];

/** Soonest open deadline first, then start time. */
export function sortKey(o: { roles: { closes: string | null; status: string }[]; start: string }): string {
  const now = meta.built;
  const deadlines = o.roles
    .filter((r) => r.closes && r.status !== "closed" && r.closes >= now)
    .map((r) => r.closes as string)
    .sort();
  return `${deadlines[0] ?? o.start}|${o.start}`;
}

export const live: Opportunity[] = [...records].sort((a, b) => sortKey(a).localeCompare(sortKey(b)));
export const liveEntries: Entry[] = [...entries].sort((a, b) => sortKey(a).localeCompare(sortKey(b)));
export const past: Opportunity[] = [...archive].sort((a, b) => b.start.localeCompare(a.start));
const byId = new Map([...records, ...archive].map((o) => [o.id, o]));

export function getOpportunity(id: string): Opportunity | undefined {
  return byId.get(id);
}

/** Same shape as the compact index built by scripts/gen-data.mjs. */
export function toEntry(o: Opportunity): Entry {
  return {
    id: o.id, type: o.type, title: o.title, organizer: o.organizer,
    roles: o.roles.map(({ role, opens, closes, status, url }) => ({ role, opens, closes, status, url })),
    start: o.start, end: o.end, timezone: o.timezone, all_day: o.all_day, mode: o.mode,
    city: o.location.city, region: o.location.region, country: o.location.country, schools: o.schools,
    near: o.near_schools.map((n) => [n.school_id, n.km] as [string, number]), eligibility: o.eligibility,
    cost: o.cost.kind, tags: o.tags, summary: o.summary, status: o.status,
    url: o.registration.url ?? o.sources[0].url, first_seen: o.first_seen, last_verified: o.last_verified,
  };
}

export function allIds(): string[] {
  return [...byId.keys()];
}

export function nextDeadline(o: { roles: { closes: string | null }[] }, now = meta.built): string | null {
  const ds = o.roles.map((r) => r.closes).filter((d): d is string => !!d && d >= now).sort();
  return ds[0] ?? null;
}

export function facets() {
  const uniq = <T,>(xs: T[]) => [...new Set(xs)];
  return {
    type: uniq(live.map((o) => o.type)).sort(),
    role: uniq(live.flatMap((o) => o.roles.map((r) => r.role))),
    mode: uniq(live.map((o) => o.mode)).sort(),
    country: uniq(live.map((o) => o.location.country).filter((x): x is string => !!x)).sort(),
    region: uniq(live.map((o) => o.location.region).filter((x): x is string => !!x)).sort(),
    school: uniq(live.flatMap((o) => [...o.schools, ...o.near_schools.map((n) => n.school_id)]))
      .filter((s) => schoolById.has(s))
      .sort((a, b) => schoolById.get(a)!.name.localeCompare(schoolById.get(b)!.name)),
    eligibility: uniq(live.flatMap((o) => o.eligibility)),
  };
}

export type Facets = ReturnType<typeof facets>;
