"use client";

import { useState } from "react";
import type { Program } from "@/lib/types";
import { Combobox } from "./Combobox";
import { Icon } from "./Icon";

const YEAR = ["High school", "First year", "Second year", "Third year", "Fourth year"];
const KIND: Record<string, string> = { program: "Program", insight: "Insight day", fellowship: "Fellowship" };

function years(ys: number[]): string {
  if (!ys.length) return "Any year (check the details)";
  return ys.map((y) => YEAR[y] ?? `Year ${y}`).join(", ");
}

const norm = (s: string) => s.toLowerCase();

/** The programs directory with a search box and year and kind filters. Without JavaScript every program shows. */
export function ProgramList({ programs }: { programs: Program[] }) {
  const [q, setQ] = useState("");
  const [year, setYear] = useState("");
  const [kind, setKind] = useState("");
  const kinds = [...new Set(programs.map((p) => p.kind))].sort();
  const words = norm(q).split(/\s+/).filter(Boolean);

  const shown = programs.filter((p) => {
    // A program that does not say which years it targets stays visible for every year.
    if (year && p.years.length && !p.years.includes(Number(year))) return false;
    if (kind && p.kind !== kind) return false;
    const hay = norm(`${p.name} ${p.organization ?? ""} ${p.who} ${p.notes ?? ""} ${p.timing ?? ""}`);
    return words.every((w) => hay.includes(w));
  });

  return (
    <>
      <form className="filters" role="search" aria-label="Filter programs" onSubmit={(ev) => ev.preventDefault()}>
        <div className="filter-row">
          <label className="grow search">
            <span className="sr-only">Search programs</span>
            <span className="search-field">
              <Icon name="search" size={18} />
              <input type="search" value={q} onChange={(ev) => setQ(ev.target.value)} placeholder="Search companies, programs…" autoComplete="off" />
            </span>
          </label>
          <Combobox label="My year" name="year" value={year} anyLabel="any year" onChange={setYear}
            options={YEAR.map((l, i) => [String(i), l])} />
          <Combobox label="Kind" name="kind" value={kind} anyLabel="all kinds" onChange={setKind}
            options={kinds.map((k) => [k, KIND[k] ?? k])} />
        </div>
      </form>
      <p className="result-count" aria-live="polite">{shown.length} of {programs.length} programs</p>
      <ul className="programs">
        {shown.map((p) => (
          <li key={p.url + p.name} className="card">
            <h2 className="card-title">
              <a href={p.url} rel="noopener">{p.name}</a>
            </h2>
            <p className="card-meta">
              {p.organization && <span>{p.organization}</span>}
              <span>For: {years(p.years)}</span>
              {p.timing && <span>When: {p.timing}</span>}
            </p>
            <p>{p.who}</p>
            {p.notes && <p className="muted">{p.notes}</p>}
            <p className="muted small">Details checked {p.checked}. Confirm dates and eligibility on the official page.</p>
          </li>
        ))}
      </ul>
      {shown.length === 0 && <p className="empty">No programs match. Try another year or clear the search.</p>}
    </>
  );
}
