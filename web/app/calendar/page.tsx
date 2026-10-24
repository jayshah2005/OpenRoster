// /calendar/: weekly agenda rendered on the server (no-JS), upgraded to a month grid by CalendarView.
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { CalendarView } from "@/components/CalendarView";
import { FilterSidebar, SidebarFallback } from "@/components/FilterSidebar";
import { facets, liveEntries, schools } from "@/lib/data";
import { fmtWhen, weekOf } from "@/lib/format";
import { TYPE_LABEL } from "@/lib/labels";
import type { Entry } from "@/lib/types";

export const metadata: Metadata = { title: "Calendar" };

export default function CalendarPage() {
  const weeks = new Map<string, Entry[]>();
  for (const e of [...liveEntries].sort((a, b) => a.start.localeCompare(b.start))) {
    const w = weekOf(e.start);
    weeks.set(w, [...(weeks.get(w) ?? []), e]);
  }
  const agenda = (
    <div className="agenda">
      {[...weeks.entries()].slice(0, 16).map(([monday, items]) => (
        <section className="week" key={monday}>
          <h2>Week of {monday}</h2>
          <ul className="agenda-list">
            {items.map((e) => (
              <li key={e.id}>
                <time dateTime={e.start}>{fmtWhen(e)}</time> · <Link href={`/o/${e.id}/`} prefetch={false}>{e.title}</Link>{" "}
                <span className={`tag tag-${e.type}`}>{TYPE_LABEL[e.type]}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {weeks.size === 0 && <p className="empty">No upcoming events yet.</p>}
    </div>
  );
  return (
    <>
      <section className="page-head">
        <h1>Calendar</h1>
        <p className="lede">Every dated listing by day. The filters on the left apply here too.</p>
      </section>
      <div className="directory">
        <aside className="dir-side" aria-label="Filters">
          <Suspense fallback={<SidebarFallback links={[]} />}>
            <FilterSidebar facets={facets()} schoolNames={Object.fromEntries(schools.map((s) => [s.id, s.name]))} />
          </Suspense>
        </aside>
        <div className="dir-main">
          <Suspense fallback={agenda}>
            <CalendarView>{agenda}</CalendarView>
          </Suspense>
        </div>
      </div>
    </>
  );
}
