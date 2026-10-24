// Filter logic shared by the browser (list and calendar) and the feed route, so a subscription link
// always returns exactly what the page shows. All state lives in the URL query string.
import type { Entry } from "./types";

export interface Filters {
  q: string;
  type: string[];
  role: string[];
  from: string;
  to: string;
  deadline: number | null;
  mode: string[];
  country: string;
  region: string;
  school: string;
  km: number | null;
  elig: string[];
  cost: string;
  /** Audience tags from the pipeline, e.g. first_year, women_nonbinary, beginner_friendly. */
  audience: string[];
  /** Only opportunities that are taking applications right now. */
  open: boolean;
}

export const FILTER_KEYS = [
  "q", "type", "role", "from", "to", "deadline", "mode", "country", "region", "school", "km", "elig", "cost",
  "for", "open",
] as const;

const list = (v: string | null) => (v ? v.split(",").map((s) => s.trim()).filter(Boolean) : []);
const num = (v: string | null) => (v && /^\d+$/.test(v) ? Number(v) : null);

export function parseFilters(p: URLSearchParams): Filters {
  return {
    q: (p.get("q") ?? "").trim().slice(0, 100),
    type: list(p.get("type")),
    role: list(p.get("role")),
    from: /^\d{4}-\d{2}-\d{2}$/.test(p.get("from") ?? "") ? p.get("from")! : "",
    to: /^\d{4}-\d{2}-\d{2}$/.test(p.get("to") ?? "") ? p.get("to")! : "",
    deadline: num(p.get("deadline")),
    mode: list(p.get("mode")),
    country: p.get("country") ?? "",
    region: p.get("region") ?? "",
    school: p.get("school") ?? "",
    km: num(p.get("km")),
    elig: list(p.get("elig")),
    cost: p.get("cost") ?? "",
    audience: list(p.get("for")),
    open: p.get("open") === "1",
  };
}

// URL key -> Filters field, where they differ ("for" is a reserved word in JS).
const FIELD: Record<string, keyof Filters> = { for: "audience" };

export function toQuery(f: Partial<Filters>): string {
  const p = new URLSearchParams();
  for (const k of FILTER_KEYS) {
    const raw = f[FIELD[k] ?? (k as keyof Filters)];
    const v = typeof raw === "boolean" ? (raw ? "1" : "") : raw;
    if (v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0)) continue;
    p.set(k, Array.isArray(v) ? v.join(",") : String(v));
  }
  return p.toString();
}

export function isEmpty(f: Filters): boolean {
  return toQuery(f) === "";
}

const norm = (s: string) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();

export function matches(e: Entry, f: Filters, now: Date): boolean {
  if (f.type.length && !f.type.includes(e.type)) return false;
  if (f.role.length && !e.roles.some((r) => f.role.includes(r.role) && r.status !== "closed")) return false;
  if (f.mode.length && !f.mode.includes(e.mode)) return false;
  if (f.country && e.country !== f.country) return false;
  if (f.region && e.region !== f.region) return false;
  if (f.cost && e.cost !== f.cost) return false;
  if (f.audience.length && !f.audience.some((t) => e.tags.includes(t) || (t === "high_school" && e.eligibility.includes("high_school")))) return false;
  if (f.open && !isOpenNow(e, now)) return false;
  if (f.elig.length && !e.eligibility.some((x) => f.elig.includes(x))) return false;
  const day = e.start.slice(0, 10);
  if (f.from && (e.end ?? e.start).slice(0, 10) < f.from) return false;
  if (f.to && day > f.to) return false;
  if (f.deadline !== null) {
    const limit = new Date(now.getTime() + f.deadline * 86_400_000).toISOString();
    const nowIso = now.toISOString();
    const relevant = e.roles.filter((r) => !f.role.length || f.role.includes(r.role));
    if (!relevant.some((r) => r.closes && r.closes >= nowIso && r.closes <= limit)) return false;
  }
  if (f.school) {
    if (f.km !== null) {
      const near = e.near.find(([s]) => s === f.school);
      const online = e.mode === "online" && e.schools.includes("open_to_all");
      if (!(near && near[1] <= f.km) && !online) return false;
    } else if (!e.schools.includes(f.school) && !e.schools.includes("open_to_all")) {
      return false;
    }
  }
  if (f.q) {
    const hay = norm(`${e.title} ${e.organizer} ${e.city ?? ""} ${e.summary} ${e.type} ${e.tags.join(" ")}`);
    if (!norm(f.q).split(/\s+/).every((w) => hay.includes(w))) return false;
  }
  return true;
}

/** Taking applications now: a role is marked open, or its window includes now. */
export function isOpenNow(e: Entry, now: Date): boolean {
  const t = now.toISOString();
  return e.roles.some((r) => {
    if (r.status === "closed" || (r.closes && r.closes < t)) return false; // a passed deadline beats a stale status
    if (r.opens && r.opens > t) return false;
    return r.status === "open" || !!r.closes;
  });
}

export function applyFilters(entries: Entry[], f: Filters, now: Date): Entry[] {
  return entries.filter((e) => matches(e, f, now));
}

export function describe(f: Filters, labels: { type: Record<string, string>; role: Record<string, string> }): string {
  const bits: string[] = [];
  if (f.type.length) bits.push(f.type.map((t) => labels.type[t] ?? t).join(" or "));
  if (f.role.length) bits.push(`as ${f.role.map((r) => labels.role[r] ?? r).join(" or ")}`);
  if (f.region) bits.push(f.region);
  if (f.school) bits.push(f.km ? `within ${f.km} km of ${f.school}` : `open to ${f.school}`);
  if (f.deadline !== null) bits.push(`deadline within ${f.deadline} days`);
  if (f.q) bits.push(`“${f.q}”`);
  return bits.join(", ") || "all upcoming";
}
