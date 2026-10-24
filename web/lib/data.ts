// Build-time data. The JSON modules are produced by scripts/gen-data.mjs from ../data and ../config,
// so the site never reads the filesystem at request time.
import archiveJson from "@/generated/archive.json";
import alsoUsefulJson from "@/generated/also-useful.json";
import indexJson from "@/generated/index.json";
import metaJson from "@/generated/meta.json";
import programsJson from "@/generated/programs.json";
import recordsJson from "@/generated/records.json";
import schoolsJson from "@/generated/schools.json";
import statusJson from "@/generated/status.json";
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

export interface PipelineStatus {
  configured: number;
  approved: number;
  enabled: number;
  audited: number;
  verdicts: Record<string, number>;
  lastRun: { runnable: number; failing: number; listings: number; held_for_review: number; last_run: string } | null;
  failing: { id: string; error: string }[];
}
/** Pipeline numbers for /status/ (scripts/gen-data.mjs reads config, audits and data/health/state.json). */
export const status = statusJson as PipelineStatus;

/** Red flags, mirroring openroster/ops/health.py: an empty or stale site must say why. */
export function redFlags(s: PipelineStatus = status, listings = records.length): string[] {
  const flags: string[] = [];
  if (s.approved === 0) {
    flags.push(`None of the ${s.configured} configured sources is approved yet, so nothing is collected. A maintainer approves sources after reading their audit.`);
  }
  if (listings === 0) flags.push("There are no listings right now.");
  if (s.lastRun && s.lastRun.runnable > 0 && s.lastRun.failing > s.lastRun.runnable / 2) {
    flags.push(`${s.lastRun.failing} of ${s.lastRun.runnable} sources failed in the last run.`);
  }
  return flags;
}

// Dates carry local offsets (-04:00, Z); compare as UTC so string order is time order.
const utc = (iso: string) => new Date(iso).toISOString();

/** Soonest open deadline first, then start time (or end time, for events already under way). */
export function sortKey(o: { roles: { closes: string | null; status: string }[]; start: string; end: string | null }): string {
  const now = utc(meta.built);
  const deadlines = o.roles
    .filter((r) => r.closes && r.status !== "closed" && utc(r.closes) >= now)
    .map((r) => utc(r.closes as string))
    .sort();
  const when = utc(o.start) >= now ? utc(o.start) : utc(o.end ?? o.start);
  return `${deadlines[0] ?? when}|${utc(o.start)}`;
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
  const ds = o.roles.map((r) => r.closes).filter((d): d is string => !!d && utc(d) >= utc(now))
    .sort((a, b) => utc(a).localeCompare(utc(b)));
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
