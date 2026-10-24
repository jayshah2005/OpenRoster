"use client";

import Link from "next/link";
import { useState } from "react";
import { TYPE_LABEL } from "@/lib/labels";
import { Combobox } from "./Combobox";
import { Icon } from "./Icon";

export type ArchiveRow = { id: string; title: string; organizer: string; type: string; date: string; year: string };

/** Past listings with search, type and year filters. Without JavaScript every row shows. */
export function ArchiveList({ rows }: { rows: ArchiveRow[] }) {
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [year, setYear] = useState("");
  const types = [...new Set(rows.map((r) => r.type))].sort();
  const years = [...new Set(rows.map((r) => r.year))].sort().reverse();
  const words = q.toLowerCase().split(/\s+/).filter(Boolean);

  const shown = rows.filter((r) => {
    if (type && r.type !== type) return false;
    if (year && r.year !== year) return false;
    const hay = `${r.title} ${r.organizer}`.toLowerCase();
    return words.every((w) => hay.includes(w));
  });

  return (
    <>
      <form className="filters" role="search" aria-label="Filter past opportunities" onSubmit={(ev) => ev.preventDefault()}>
        <div className="filter-row">
          <label className="grow search">
            <span className="sr-only">Search past opportunities</span>
            <span className="search-field">
              <Icon name="search" size={18} />
              <input type="search" value={q} onChange={(ev) => setQ(ev.target.value)} placeholder="Search titles and organizers…" autoComplete="off" />
            </span>
          </label>
          <Combobox label="Type" name="type" value={type} anyLabel="all types" onChange={setType}
            options={types.map((t) => [t, TYPE_LABEL[t as keyof typeof TYPE_LABEL] ?? t])} />
          <Combobox label="Year" name="year" value={year} anyLabel="any year" onChange={setYear}
            options={years.map((y) => [y, y])} />
        </div>
      </form>
      <p className="result-count" aria-live="polite">{shown.length} of {rows.length} past listings</p>
      {shown.length > 0 && (
        <ul className="agenda-list">
          {shown.map((r) => (
            <li key={r.id}>
              {r.date} · <Link href={`/o/${r.id}/`} prefetch={false}>{r.title}</Link> · {r.organizer}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
