import type { Metadata } from "next";
import { CardList, nextDeadline } from "@/components/Card";
import { liveEntries, meta } from "@/lib/data";
import { weekOf } from "@/lib/format";

export const metadata: Metadata = { title: "This week" };

const DAY = 86_400_000;

export default function DigestPage() {
  // "Now" is the data build time: the page is rebuilt on every data refresh (every 6 hours).
  const now = meta.built;
  const monday = weekOf(now);
  const weekStart = `${monday}T00:00:00`;
  const weekEnd = new Date(new Date(`${monday}T12:00:00Z`).getTime() + 7 * DAY).toISOString().slice(0, 10);
  const in14 = new Date(new Date(now).getTime() + 14 * DAY).toISOString();
  const weekAgo = new Date(new Date(now).getTime() - 7 * DAY).toISOString();

  const deadlines = liveEntries
    .filter((e) => {
      const d = nextDeadline(e, now);
      return d !== null && d <= in14;
    })
    .sort((a, b) => (nextDeadline(a, now) ?? "").localeCompare(nextDeadline(b, now) ?? ""));
  const thisWeek = liveEntries
    .filter((e) => e.start >= weekStart && e.start.slice(0, 10) < weekEnd)
    .sort((a, b) => a.start.localeCompare(b.start));
  const fresh = liveEntries.filter((e) => e.first_seen >= weekAgo).sort((a, b) => a.start.localeCompare(b.start));

  return (
    <>
      <h1>This week · week of {monday}</h1>
      <p>
        Deadlines first. Updated with every data refresh. <a href="/feeds/digest.rss">RSS for new listings</a> ·{" "}
        <a href="/feeds/new-today.rss">New today (RSS)</a>
      </p>
      <section aria-labelledby="dl-h">
        <h2 id="dl-h">Deadlines in the next 14 days ({deadlines.length})</h2>
        <CardList items={deadlines} nowIso={now} />
      </section>
      <section aria-labelledby="wk-h">
        <h2 id="wk-h">Happening this week ({thisWeek.length})</h2>
        <CardList items={thisWeek} nowIso={now} />
      </section>
      <section aria-labelledby="new-h">
        <h2 id="new-h">New this week ({fresh.length})</h2>
        <CardList items={fresh} nowIso={now} />
      </section>
    </>
  );
}
