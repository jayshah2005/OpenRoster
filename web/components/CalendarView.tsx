"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type ReactNode, useMemo, useState } from "react";
import { applyFilters, parseFilters, toQuery } from "@/lib/filter";
import { TYPE_LABEL } from "@/lib/labels";
import type { Entry } from "@/lib/types";
import { SubscribeLinks } from "./Results";
import { useIndex } from "./useIndex";

const TZ = "America/Toronto";
const dayKey = (iso: string) =>
  new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(iso));

/** Month grid built in the browser; the server-rendered weekly agenda is the no-JS fallback. */
export function CalendarView({ children }: { children: ReactNode }) {
  const qs = useSearchParams().toString();
  const index = useIndex(true);
  const [offset, setOffset] = useState(0);
  const f = useMemo(() => parseFilters(new URLSearchParams(qs)), [qs]);

  const { label, cells, byDay } = useMemo(() => {
    const now = new Date();
    const first = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + offset, 1, 12));
    const startDow = (first.getUTCDay() + 6) % 7;
    const daysInMonth = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
    const cells: (string | null)[] = Array(startDow).fill(null);
    for (let d = 1; d <= daysInMonth; d++) {
      cells.push(new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth(), d, 12)).toISOString().slice(0, 10));
    }
    while (cells.length % 7) cells.push(null);
    const byDay = new Map<string, Entry[]>();
    for (const e of applyFilters(index ?? [], f, now)) {
      const k = dayKey(e.start);
      byDay.set(k, [...(byDay.get(k) ?? []), e]);
    }
    const label = new Intl.DateTimeFormat("en-CA", { month: "long", year: "numeric", timeZone: "UTC" }).format(first);
    return { label, cells, byDay };
  }, [index, offset, f]);

  if (!index) return <>{children}</>;

  return (
    <section className="month" aria-label={`Calendar for ${label}`}>
      <div className="month-nav">
        <button type="button" onClick={() => setOffset((o) => o - 1)} aria-label="Previous month">←</button>
        <h2>{label}</h2>
        <button type="button" onClick={() => setOffset((o) => o + 1)} aria-label="Next month">→</button>
      </div>
      <div className="grid" role="grid">
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
          <div key={d} className="dow" role="columnheader">{d}</div>
        ))}
        {cells.map((day, i) => (
          <div key={day ?? `pad-${i}`} className={`cell${day ? "" : " pad"}`} role="gridcell">
            {day && (
              <>
                <span className="day-num">{Number(day.slice(8))}</span>
                <ul>
                  {(byDay.get(day) ?? []).slice(0, 4).map((e) => (
                    <li key={e.id} className={`tag-${e.type}`}>
                      <Link href={`/o/${e.id}/`} prefetch={false} title={`${TYPE_LABEL[e.type]}: ${e.title}`}>{e.title}</Link>
                    </li>
                  ))}
                  {(byDay.get(day)?.length ?? 0) > 4 && <li className="more">+{byDay.get(day)!.length - 4} more</li>}
                </ul>
              </>
            )}
          </div>
        ))}
      </div>
      <SubscribeLinks query={toQuery(f)} />
    </section>
  );
}
