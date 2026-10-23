import { describe, expect, it } from "vitest";
import { applyFilters, parseFilters, toQuery } from "@/lib/filter";
import { toICS, toRSS } from "@/lib/feeds";
import type { Entry } from "@/lib/types";

const base: Entry = {
  id: "2026-11-herhacks-1234",
  type: "hackathon",
  title: "HerHacks Hackathon",
  organizer: "BMO",
  roles: [
    { role: "participant", opens: null, closes: "2026-11-20T23:59:00-05:00", status: "open", url: null },
    { role: "mentor", opens: null, closes: "2026-11-10T23:59:00-05:00", status: "open", url: "https://forms.gle/x" },
  ],
  start: "2026-11-28T09:00:00-05:00",
  end: "2026-11-28T18:00:00-05:00",
  timezone: "America/Toronto",
  all_day: false,
  mode: "in_person",
  city: "Toronto",
  region: "CA-ON",
  country: "CA",
  schools: ["open_to_all"],
  near: [["uoft", 2.1], ["brock", 95.4]],
  eligibility: ["undergrad"],
  cost: "free",
  tags: [],
  summary: "Hackathon hosted by BMO (Toronto).",
  status: "scheduled",
  url: "https://jobs.bmo.com/ca/en/student-events",
  first_seen: "2026-10-23T12:00:00Z",
  last_verified: "2026-10-23T12:00:00Z",
};
const online: Entry = { ...base, id: "web", title: "AI webinar", type: "tech_talk", mode: "online", city: null, near: [], roles: [base.roles[0]] };
const NOW = new Date("2026-11-05T12:00:00Z");
const run = (q: string) => applyFilters([base, online], parseFilters(new URLSearchParams(q)), NOW).map((e) => e.id);

describe("filters", () => {
  it("round-trips through the URL", () => {
    const f = parseFilters(new URLSearchParams("type=hackathon&role=mentor&deadline=7&school=brock&km=100&q=bmo"));
    expect(parseFilters(new URLSearchParams(toQuery(f)))).toEqual(f);
  });
  it("filters by type, role and mode", () => {
    expect(run("type=hackathon")).toEqual([base.id]);
    expect(run("role=mentor")).toEqual([base.id]);
    expect(run("mode=online")).toEqual(["web"]);
  });
  it("deadline within N days applies to the chosen role", () => {
    expect(run("deadline=7")).toEqual([base.id]); // mentor closes Nov 10
    expect(run("deadline=7&role=participant")).toEqual([]); // participant closes Nov 20
  });
  it("near a school uses distance; online open-to-all events count as near", () => {
    expect(run("school=brock&km=50")).toEqual(["web"]);
    expect(run("school=brock&km=100")).toEqual([base.id, "web"]);
  });
  it("free-text search ignores case and accents", () => {
    expect(run("q=herhacks bmo")).toEqual([base.id]);
    expect(run("q=nothing-like-this")).toEqual([]);
  });
  it("ignores malformed values", () => {
    const f = parseFilters(new URLSearchParams("from=yesterday&deadline=abc"));
    expect(f.from).toBe("");
    expect(f.deadline).toBeNull();
  });
});

describe("feeds", () => {
  it("writes valid iCalendar with folded lines and UTC times", () => {
    const ics = toICS([base], "test");
    expect(ics.startsWith("BEGIN:VCALENDAR\r\n")).toBe(true);
    expect(ics).toContain("DTSTART:20261128T140000Z");
    expect(ics).toContain("UID:2026-11-herhacks-1234@openroster");
    for (const line of ics.split("\r\n")) expect(new TextEncoder().encode(line).length).toBeLessThanOrEqual(75);
  });
  it("writes all-day events as dates with an exclusive end", () => {
    const ics = toICS([{ ...base, all_day: true, start: "2026-11-28T00:00:00-05:00", end: null }], "t");
    expect(ics).toContain("DTSTART;VALUE=DATE:20261128");
    expect(ics).toContain("DTEND;VALUE=DATE:20261129");
  });
  it("escapes RSS", () => {
    const rss = toRSS([{ ...base, title: "R&D <night>" }], "t", "https://x");
    expect(rss).toContain("R&amp;D &lt;night&gt;");
  });
});
