import { describe, expect, it } from "vitest";
import { type Item, countBy, itemMatches, programMatches, sortItems } from "@/lib/directory";
import { matchesYear, parseFilters } from "@/lib/filter";
import type { Entry, Program } from "@/lib/types";

const event = (over: Partial<Entry>): Entry => ({
  id: "e", type: "hackathon", title: "Hack", organizer: "Org", roles: [], start: "2026-11-28T09:00:00-05:00", end: null,
  timezone: "America/Toronto", all_day: false, mode: "in_person", city: "Toronto", region: "CA-ON", country: "CA",
  schools: ["open_to_all"], near: [], eligibility: ["undergrad"], cost: "free", tags: [], summary: "", status: "scheduled",
  url: "https://example.com", first_seen: "2026-10-01T00:00:00Z", last_verified: "2026-10-01T00:00:00Z", ...over,
});
const program = (over: Partial<Program>): Program => ({
  name: "Insight Day", organization: "Bank", url: "https://example.com/p", kind: "insight", timing: null,
  who: "First-year students", years: [1], link_only: false, notes: null, checked: "2026-10-23", ...over,
});
const f = (q: string) => parseFilters(new URLSearchParams(q));
const NOW = new Date("2026-11-05T12:00:00Z");

describe("year of study", () => {
  it("keeps year-tagged events to those years and treats unstated eligibility as open to undergrads", () => {
    const firstYears = event({ tags: ["first_year"] });
    expect(matchesYear(firstYears, 1)).toBe(true);
    expect(matchesYear(firstYears, 3)).toBe(false);
    expect(matchesYear(event({ eligibility: ["unknown"] }), 4)).toBe(true);
    expect(matchesYear(event({ eligibility: ["undergrad"] }), 0)).toBe(false);
    expect(matchesYear(event({ eligibility: ["high_school"] }), 0)).toBe(true);
    expect(matchesYear(event({ eligibility: ["grad"] }), 5)).toBe(true);
  });

  it("is a URL filter like the others", () => {
    expect(f("year=3").year).toBe("3");
    expect(f("year=9").year).toBe("");
  });
});

describe("programs in the directory", () => {
  it("match by year, search and the program type", () => {
    const p = program({ years: [3, 4] });
    expect(programMatches(p, f("year=3"))).toBe(true);
    expect(programMatches(p, f("year=1"))).toBe(false);
    expect(programMatches(program({ years: [] }), f("year=2"))).toBe(true); // any year
    expect(programMatches(p, f("type=program"))).toBe(true);
    expect(programMatches(p, f("type=hackathon"))).toBe(false);
    expect(programMatches(p, f("q=bank insight"))).toBe(true);
  });

  it("are hidden by filters they have no facts for, rather than guessed", () => {
    for (const q of ["region=CA-ON", "deadline=7", "from=2026-11-01", "mode=online", "open=1", "cost=free", "role=volunteer"]) {
      expect(programMatches(program({}), f(q))).toBe(false);
    }
  });

  it("sort after events, and counts reflect every other filter", () => {
    const items: Item[] = [
      { kind: "program", p: program({ name: "B" }) },
      { kind: "event", e: event({ id: "late", start: "2026-12-01T09:00:00-05:00" }) },
      { kind: "event", e: event({ id: "soon", type: "workshop", start: "2026-11-10T09:00:00-05:00" }) },
    ];
    const order = sortItems(items, "start", NOW).map((i) => (i.kind === "event" ? i.e.id : i.p.name));
    expect(order).toEqual(["soon", "late", "B"]);
    expect(countBy(items, f("type=hackathon"), "type", ["hackathon", "workshop", "program"], NOW))
      .toEqual({ hackathon: 1, workshop: 1, program: 1 });
    expect(items.filter((i) => itemMatches(i, f("type=workshop,program"), NOW))).toHaveLength(2);
  });
});

describe("deadline-first order", () => {
  it("sorts an event already under way by its end, not its long-past start", () => {
    const ongoing = event({ id: "ongoing", start: "2026-10-01T08:00:00-04:00", end: "2026-11-30T17:00:00-05:00" });
    const soon = event({ id: "soon", start: "2026-11-10T09:00:00-05:00" });
    const order = sortItems([{ kind: "event", e: ongoing }, { kind: "event", e: soon }], "deadline", NOW)
      .map((i) => (i.kind === "event" ? i.e.id : ""));
    expect(order).toEqual(["soon", "ongoing"]);
  });
});
