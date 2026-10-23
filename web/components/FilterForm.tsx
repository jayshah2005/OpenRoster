"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { type ChangeEvent, type FormEvent, useRef, useState } from "react";
import { type Filters, parseFilters, toQuery } from "@/lib/filter";
import { COUNTRY_LABEL, ELIG_LABEL, MODE_LABEL, REGION_LABEL, TYPE_LABEL } from "@/lib/labels";
import type { Facets } from "@/lib/data";

type Props = { facets: Facets; schoolNames: Record<string, string> };

const ROLE_OPTIONS: [string, string][] = [
  ["participant", "attend"], ["volunteer", "volunteer"], ["mentor", "mentor"], ["judge", "judge"],
  ["organizer_team", "organize"], ["workshop_lead", "lead a workshop"],
];

export function FilterForm({ facets, schoolNames }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const f = parseFilters(new URLSearchParams(params.toString()));
  const [q, setQ] = useState(f.q);
  const [urlQ, setUrlQ] = useState(f.q);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const advancedSet = !!(f.from || f.to || f.deadline !== null || f.mode.length || f.country || f.region ||
    f.school || f.elig.length || f.cost);

  // When the URL's search term changes from outside the box (back button, "Clear filters"), follow it.
  if (f.q !== urlQ) {
    setUrlQ(f.q);
    setQ(f.q);
  }

  function update(patch: Partial<Filters>) {
    const next = toQuery({ ...f, ...patch });
    router.replace(next ? `${pathname}?${next}` : pathname, { scroll: false });
  }

  const sel = (key: keyof Filters) => (ev: ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const v = ev.target.value;
    if (["type", "role", "mode", "elig"].includes(key)) update({ [key]: v ? [v] : [] } as Partial<Filters>);
    else if (key === "deadline" || key === "km") update({ [key]: v ? Number(v) : null } as Partial<Filters>);
    else update({ [key]: v } as Partial<Filters>);
  };

  function onSearch(ev: ChangeEvent<HTMLInputElement>) {
    setQ(ev.target.value);
    if (timer.current) clearTimeout(timer.current);
    const v = ev.target.value;
    timer.current = setTimeout(() => update({ q: v }), 250);
  }

  function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    update({ q });
  }

  return (
    <form className="filters" role="search" aria-label="Filter opportunities" onSubmit={onSubmit}>
      <div className="filter-row">
        <label className="grow">
          Search
          <input type="search" name="q" value={q} onChange={onSearch} placeholder="hackathon, Google, Brock…" autoComplete="off" />
        </label>
        <label>
          I want to
          <select name="role" value={f.role[0] ?? ""} onChange={sel("role")}>
            <option value="">do anything</option>
            {ROLE_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>
          Type
          <select name="type" value={f.type[0] ?? ""} onChange={sel("type")}>
            <option value="">all types</option>
            {facets.type.map((t) => <option key={t} value={t}>{TYPE_LABEL[t]}</option>)}
          </select>
        </label>
      </div>
      <details className="more-filters" open={advancedSet || undefined}>
        <summary>More filters</summary>
        <div className="filter-grid">
          <label>From<input type="date" name="from" value={f.from} onChange={sel("from")} /></label>
          <label>To<input type="date" name="to" value={f.to} onChange={sel("to")} /></label>
          <label>
            Deadline within
            <select name="deadline" value={f.deadline ?? ""} onChange={sel("deadline")}>
              <option value="">any time</option>
              {[3, 7, 14, 30].map((d) => <option key={d} value={d}>{d} days</option>)}
            </select>
          </label>
          <label>
            Mode
            <select name="mode" value={f.mode[0] ?? ""} onChange={sel("mode")}>
              <option value="">any</option>
              {facets.mode.map((m) => <option key={m} value={m}>{MODE_LABEL[m]}</option>)}
            </select>
          </label>
          <label>
            Country
            <select name="country" value={f.country} onChange={sel("country")}>
              <option value="">any</option>
              {facets.country.map((c) => <option key={c} value={c}>{COUNTRY_LABEL[c] ?? c}</option>)}
            </select>
          </label>
          <label>
            Province / state
            <select name="region" value={f.region} onChange={sel("region")}>
              <option value="">any</option>
              {facets.region.map((r) => <option key={r} value={r}>{REGION_LABEL[r] ?? r}</option>)}
            </select>
          </label>
          <label>
            School
            <select name="school" value={f.school} onChange={sel("school")}>
              <option value="">any</option>
              {facets.school.map((s) => <option key={s} value={s}>{schoolNames[s] ?? s}</option>)}
            </select>
          </label>
          <label>
            Distance
            <select name="km" value={f.km ?? ""} onChange={sel("km")} disabled={!f.school}>
              <option value="">open to its students</option>
              {[25, 50, 100].map((k) => <option key={k} value={k}>within {k} km</option>)}
            </select>
          </label>
          <label>
            Eligibility
            <select name="elig" value={f.elig[0] ?? ""} onChange={sel("elig")}>
              <option value="">any</option>
              {facets.eligibility.map((e) => <option key={e} value={e}>{ELIG_LABEL[e]}</option>)}
            </select>
          </label>
          <label>
            Cost
            <select name="cost" value={f.cost} onChange={sel("cost")}>
              <option value="">any</option>
              <option value="free">free</option>
              <option value="paid">paid</option>
            </select>
          </label>
        </div>
      </details>
      <div className="filter-actions">
        <button type="button" className="link-button" onClick={() => router.replace(pathname, { scroll: false })}>
          Clear filters
        </button>
      </div>
    </form>
  );
}

export function FilterFormFallback() {
  return (
    <div className="filters filters-static">
      <p className="hint">
        Filters need JavaScript. You can still browse by type, role, region or school with the links at the bottom of
        the page, or subscribe to a feed.
      </p>
    </div>
  );
}
