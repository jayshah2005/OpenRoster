"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { type ChangeEvent, type FormEvent, useRef, useState } from "react";
import { type Filters, parseFilters, toQuery } from "@/lib/filter";
import { AUDIENCE_LABEL, COUNTRY_LABEL, ELIG_LABEL, MODE_LABEL, REGION_LABEL, TYPE_LABEL } from "@/lib/labels";
import type { Facets } from "@/lib/data";
import { Combobox } from "./Combobox";
import { Icon } from "./Icon";

type Props = { facets: Facets; schoolNames: Record<string, string> };

const ROLE_OPTIONS: [string, string][] = [
  ["participant", "attend"], ["volunteer", "volunteer"], ["mentor", "mentor"], ["judge", "judge"],
  ["organizer_team", "organize"], ["workshop_lead", "lead a workshop"],
];
const DEADLINE_OPTIONS: [string, string][] = [3, 7, 14, 30].map((d) => [String(d), `${d} days`]);
const KM_OPTIONS: [string, string][] = [25, 50, 100].map((k) => [String(k), `within ${k} km`]);

export function FilterForm({ facets, schoolNames }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const f = parseFilters(new URLSearchParams(params.toString()));
  const [q, setQ] = useState(f.q);
  const [urlQ, setUrlQ] = useState(f.q);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const advancedSet = !!(f.from || f.to || f.deadline !== null || f.mode.length || f.country || f.region ||
    f.school || f.elig.length || f.cost || f.audience.length);

  // When the URL's search term changes from outside the box (back button, "Clear filters"), follow it.
  if (f.q !== urlQ) {
    setUrlQ(f.q);
    setQ(f.q);
  }

  function update(patch: Partial<Filters>) {
    const next = toQuery({ ...f, ...patch });
    router.replace(next ? `${pathname}?${next}` : pathname, { scroll: false });
  }

  // Single-pick fields that the URL stores as lists (type=hackathon,workshop is still valid in a shared link).
  const pickList = (key: "type" | "role" | "mode" | "elig" | "audience") => (v: string) =>
    update({ [key]: v ? [v] : [] });

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
        <label className="grow search">
          <span className="sr-only">Search</span>
          <span className="search-field">
            <Icon name="search" size={18} />
            <input type="search" name="q" value={q} onChange={onSearch} placeholder="Search hackathons, companies, schools…" autoComplete="off" />
          </span>
        </label>
        <Combobox label="I want to" name="role" value={f.role[0] ?? ""} anyLabel="do anything"
          options={ROLE_OPTIONS} onChange={pickList("role")} />
        <Combobox label="Type" name="type" value={f.type[0] ?? ""} anyLabel="all types"
          options={facets.type.map((t) => [t, TYPE_LABEL[t]])} onChange={pickList("type")} />
      </div>
      <label className="check">
        <input type="checkbox" name="open" checked={f.open} onChange={(ev) => update({ open: ev.target.checked })} />
        Only show what is open for applications now
      </label>
      <details className="more-filters" open={advancedSet || undefined}>
        <summary>More filters</summary>
        <div className="filter-grid">
          <label>From<input type="date" name="from" value={f.from} onChange={(ev) => update({ from: ev.target.value })} /></label>
          <label>To<input type="date" name="to" value={f.to} onChange={(ev) => update({ to: ev.target.value })} /></label>
          <Combobox label="Deadline within" name="deadline" value={String(f.deadline ?? "")} anyLabel="any time"
            options={DEADLINE_OPTIONS} onChange={(v) => update({ deadline: v ? Number(v) : null })} />
          <Combobox label="Mode" name="mode" value={f.mode[0] ?? ""} anyLabel="any"
            options={facets.mode.map((m) => [m, MODE_LABEL[m]])} onChange={pickList("mode")} />
          <Combobox label="Country" name="country" value={f.country} anyLabel="any"
            options={facets.country.map((c) => [c, COUNTRY_LABEL[c] ?? c])} onChange={(v) => update({ country: v })} />
          <Combobox label="Province / state" name="region" value={f.region} anyLabel="any"
            options={facets.region.map((r) => [r, REGION_LABEL[r] ?? r])} onChange={(v) => update({ region: v })} />
          <Combobox label="School" name="school" value={f.school} anyLabel="any"
            options={facets.school.map((x) => [x, schoolNames[x] ?? x])}
            onChange={(v) => update({ school: v, km: v ? f.km : null })} />
          <Combobox label="Distance" name="km" value={String(f.km ?? "")} anyLabel="open to its students"
            options={KM_OPTIONS} onChange={(v) => update({ km: v ? Number(v) : null })} disabled={!f.school} />
          <Combobox label="Who it's for" name="for" value={f.audience[0] ?? ""} anyLabel="everyone"
            options={Object.entries(AUDIENCE_LABEL)} onChange={pickList("audience")} />
          <Combobox label="Eligibility" name="elig" value={f.elig[0] ?? ""} anyLabel="any"
            options={facets.eligibility.map((e) => [e, ELIG_LABEL[e]])} onChange={pickList("elig")} />
          <Combobox label="Cost" name="cost" value={f.cost} anyLabel="any"
            options={[["free", "free"], ["paid", "paid"]]} onChange={(v) => update({ cost: v })} />
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
        Filters need JavaScript. You can still browse by type, role, region or school from the links on the home page,
        or subscribe to a feed.
      </p>
    </div>
  );
}
