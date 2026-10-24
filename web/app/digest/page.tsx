// /digest/: this week's deadlines, events and new listings, rebuilt with every data refresh.
import type { Metadata } from "next";
import { Suspense } from "react";
import { CardList, nextDeadline } from "@/components/Card";
import { FilterForm, FilterFormFallback } from "@/components/FilterForm";
import { Results } from "@/components/Results";
import { facets, liveEntries, meta, schools } from "@/lib/data";
import type { Entry } from "@/lib/types";
import { fmtDate, weekOf } from "@/lib/format";

export const metadata: Metadata = { title: "This week" };

const DAY = 86_400_000;

// One digest section: the full list from the build, narrowed in the browser when filters are set.
function Section({ id, title, items, now }: { id: string; title: string; items: Entry[]; now: string }) {
  const list = <CardList items={items} nowIso={now} />;
  return (
    <section aria-labelledby={id}>
      <h2 id={id}>{title} ({items.length})</h2>
      <Suspense fallback={list}>
        <Results within={items.map((e) => e.id)}>{list}</Results>
      </Suspense>
    </section>
  );
}

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
      <h1>This week</h1>
      <p className="lede">
        Week of {fmtDate(`${monday}T12:00:00Z`)}. Deadlines first, updated with every data refresh. <a href="/feeds/digest.rss">RSS for new listings</a> ·{" "}
        <a href="/feeds/new-today.rss">New today (RSS)</a>
      </p>
      <Suspense fallback={<FilterFormFallback />}>
        <FilterForm facets={facets()} schoolNames={Object.fromEntries(schools.map((x) => [x.id, x.name]))} />
      </Suspense>
      <Section id="dl-h" title="Deadlines in the next 14 days" items={deadlines} now={now} />
      <Section id="wk-h" title="Happening this week" items={thisWeek} now={now} />
      <Section id="new-h" title="New this week" items={fresh} now={now} />
    </>
  );
}
