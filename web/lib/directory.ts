// The directory: dated events and recurring programs in one filterable list. Events use the shared filter logic
// (lib/filter.ts, also used by the feeds); programs have no date or place, so only some filters apply to them.
import { type Filters, matches } from "./filter";
import type { Entry, Program } from "./types";

/** The "type" filter value that selects recurring programs (config/programs.yaml). */
export const PROGRAM = "program";

export type Item = { kind: "event"; e: Entry } | { kind: "program"; p: Program };

export const YEAR_LABEL = ["High school", "First year", "Second year", "Third year", "Fourth year"];

export function programSlug(p: Program): string {
  return p.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

// Audience tags that map onto a program's years of study (0 = high school).
const AUDIENCE_YEAR: Record<string, number> = { high_school: 0, first_year: 1, second_year: 2 };

/**
 * Whether a program fits the filters. Filters about dates, places, cost or application windows need facts that
 * programs do not have, so setting one hides programs rather than guessing.
 */
export function programMatches(p: Program, f: Filters): boolean {
  if (f.type.length && !f.type.includes(PROGRAM)) return false;
  if (f.role.length && !f.role.includes("participant")) return false;
  if (f.from || f.to || f.deadline !== null || f.mode.length || f.country || f.region || f.school || f.cost || f.open) {
    return false;
  }
  const anyYear = p.years.length === 0;
  if (f.year && !(anyYear ? f.year !== "0" : p.years.includes(Number(f.year)))) return false;
  if (f.audience.length) {
    const ok = f.audience.some((a) => a in AUDIENCE_YEAR && (anyYear || p.years.includes(AUDIENCE_YEAR[a])));
    if (!ok) return false;
  }
  if (f.elig.length) {
    const ok = f.elig.some((x) =>
      x === "high_school" ? p.years.includes(0)
        : x === "undergrad" ? anyYear || p.years.some((y) => y >= 1)
          : x === "open_to_all" ? anyYear : false);
    if (!ok) return false;
  }
  if (f.q) {
    const hay = `${p.name} ${p.organization ?? ""} ${p.who} ${p.notes ?? ""} ${p.timing ?? ""} program`.toLowerCase();
    if (!f.q.toLowerCase().split(/\s+/).every((w) => hay.includes(w))) return false;
  }
  return true;
}

export function itemMatches(it: Item, f: Filters, now: Date): boolean {
  return it.kind === "event" ? matches(it.e, f, now) : programMatches(it.p, f);
}

export type Sort = "deadline" | "start" | "new";
export const SORT_LABEL: Record<Sort, string> = { deadline: "Deadline first", start: "Starting soonest", new: "Newest" };

// Dates arrive with local offsets (-04:00, -05:00); compare them as UTC so string order is time order.
const utc = (iso: string) => new Date(iso).toISOString();

function nextOpenDeadline(e: Entry, nowIso: string): string | null {
  return e.roles.filter((r) => r.status !== "closed" && r.closes && utc(r.closes) >= nowIso).map((r) => utc(r.closes!)).sort()[0] ?? null;
}

/** Events in the chosen order, then programs by name (they have no dates to sort by). */
export function sortItems(items: Item[], sort: Sort, now: Date): Item[] {
  const nowIso = now.toISOString();
  // An event already under way sorts by when it ends, so a month-long one that began weeks ago doesn't sit on top.
  const when = (e: Entry) => (utc(e.start) >= nowIso ? utc(e.start) : utc(e.end ?? e.start));
  const key = (e: Entry) =>
    sort === "new" ? utc(e.first_seen) : sort === "start" ? when(e) : `${nextOpenDeadline(e, nowIso) ?? when(e)}|${utc(e.start)}`;
  const events = items.filter((i) => i.kind === "event") as Extract<Item, { kind: "event" }>[];
  const programs = items.filter((i) => i.kind === "program") as Extract<Item, { kind: "program" }>[];
  events.sort((a, b) => key(a.e).localeCompare(key(b.e)));
  if (sort === "new") events.reverse();
  programs.sort((a, b) => a.p.name.localeCompare(b.p.name));
  return [...events, ...programs];
}

/**
 * How many items each option of one filter group would show, given every other filter: the numbers next to the
 * checkboxes. `key` is the Filters field; the option is tried on its own in place of the current selection.
 */
export function countBy(items: Item[], f: Filters, key: keyof Filters, options: string[], now: Date): Record<string, number> {
  const out: Record<string, number> = {};
  for (const o of options) {
    const trial = { ...f, [key]: Array.isArray(f[key]) ? [o] : o } as Filters;
    out[o] = items.reduce((n, it) => n + (itemMatches(it, trial, now) ? 1 : 0), 0);
  }
  return out;
}
