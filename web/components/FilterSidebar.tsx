"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Facets } from "@/lib/data";
import { type Item, PROGRAM, countBy } from "@/lib/directory";
import type { Filters } from "@/lib/filter";
import {
  AUDIENCE_LABEL, COUNTRY_LABEL, ELIG_LABEL, MODE_LABEL, REGION_LABEL, ROLE_LABEL, TYPE_PLURAL, YEAR_OF_STUDY,
} from "@/lib/labels";
import type { Program } from "@/lib/types";
import { Combobox } from "./Combobox";
import { Icon } from "./Icon";
import { useFilters, useSavedFilters } from "./useFilters";
import { useIndex } from "./useIndex";

type Props = {
  facets: Facets;
  schoolNames: Record<string, string>;
  /** Recurring programs, when this page lists them (the directory does; the calendar and digest don't). */
  programs?: Program[];
  baseQuery?: string;
};

type ListKey = "type" | "role" | "audience" | "mode" | "elig";

const DEADLINE_OPTIONS: [string, string][] = [3, 7, 14, 30].map((d) => [String(d), `${d} days`]);
const KM_OPTIONS: [string, string][] = [25, 50, 100].map((k) => [String(k), `within ${k} km`]);
const COLLAPSED = 6;

/** The left column: checkbox groups with live counts, typeable dropdowns for long lists, and dates. */
export function FilterSidebar({ facets, schoolNames, programs, baseQuery = "" }: Props) {
  const { f, own, locked, active, update, clear } = useFilters(baseQuery);
  const restored = useSavedFilters(baseQuery);
  const index = useIndex(true);
  const [open, setOpen] = useState(false); // phones: the sidebar folds into a button
  const now = useMemo(() => new Date(), []);

  const items = useMemo<Item[] | null>(
    () => index && [
      ...index.map((e) => ({ kind: "event" as const, e })),
      ...(programs ?? []).map((p) => ({ kind: "program" as const, p })),
    ],
    [index, programs],
  );

  const groups: { key: ListKey; title: string; options: [string, string][] }[] = [
    {
      key: "type", title: "What",
      options: [
        ...(programs?.length ? [[PROGRAM, "Recurring programs"] as [string, string]] : []),
        ...facets.type.map((t) => [t, TYPE_PLURAL[t] ?? t] as [string, string]),
      ],
    },
    { key: "role", title: "I want to", options: Object.keys(ROLE_LABEL).filter((r) => (facets.role as string[]).includes(r)).map((r) => [r, ROLE_LABEL[r]]) },
    { key: "audience", title: "Who it's for", options: Object.entries(AUDIENCE_LABEL) },
    { key: "mode", title: "Format", options: facets.mode.map((m) => [m, MODE_LABEL[m] ?? m]) },
    { key: "elig", title: "Eligibility", options: facets.eligibility.map((e) => [e, ELIG_LABEL[e] ?? e]) },
  ];
  const urlKey: Record<ListKey, string> = { type: "type", role: "role", audience: "for", mode: "mode", elig: "elig" };

  const activeCount = (Object.keys(own) as (keyof Filters)[]).filter((k) => {
    const v = own[k];
    return k !== "q" && (Array.isArray(v) ? v.length > 0 : v !== "" && v !== null && v !== false);
  }).length;

  return (
    <div className={`sidebar${open ? " is-open" : ""}`}>
      <div className="sidebar-head">
        <h2 className="sidebar-title">Filters</h2>
        <button type="button" className="sidebar-toggle" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
          <Icon name="filter" size={16} /> Filters{activeCount ? ` (${activeCount})` : ""}
        </button>
        {active && <button type="button" className="link-button" onClick={clear}>Clear all</button>}
      </div>

      <form className="sidebar-body filters" aria-label="Filter opportunities" onSubmit={(ev) => ev.preventDefault()}>
        {restored && active && (
          <p className="saved-note">Showing your saved filters. <button type="button" className="link-button" onClick={clear}>Start fresh</button></p>
        )}

        <div className="fgroup">
          <Combobox label="My year of study" name="year" value={f.year} anyLabel="any year" options={YEAR_OF_STUDY}
            onChange={(v) => update({ year: v })} />
        </div>

        <div className="toggles">
          <label className="check">
            <input type="checkbox" checked={f.open} onChange={(ev) => update({ open: ev.target.checked })} />
            Open for applications now
          </label>
          {!locked.has("cost") && (
            <label className="check">
              <input type="checkbox" checked={f.cost === "free"} onChange={(ev) => update({ cost: ev.target.checked ? "free" : "" })} />
              Free only
            </label>
          )}
        </div>

        {groups.map((g) => {
          if (locked.has(urlKey[g.key])) return null;
          const counts = items ? countBy(items, f, g.key, g.options.map(([v]) => v), now) : null;
          const selected = f[g.key] as string[];
          // Hide options nothing matches, unless picked, so the list only offers real choices.
          const shown = g.options.filter(([v]) => !counts || counts[v] > 0 || selected.includes(v));
          if (!shown.length) return null;
          return (
            <CheckGroup key={g.key} title={g.title} options={shown} selected={selected} counts={counts}
              onChange={(next) => update({ [g.key]: next } as Partial<Filters>)} />
          );
        })}

        {(!locked.has("region") || !locked.has("country")) && (facets.region.length > 0 || facets.country.length > 0) && (
          <fieldset className="fgroup">
            <legend>Where</legend>
            {!locked.has("country") && facets.country.length > 1 && (
              <Combobox label="Country" name="country" value={f.country} anyLabel="any country"
                options={facets.country.map((c) => [c, COUNTRY_LABEL[c] ?? c])} onChange={(v) => update({ country: v })} />
            )}
            {!locked.has("region") && (
              <Combobox label="Province / state" name="region" value={f.region} anyLabel="anywhere"
                options={facets.region.map((r) => [r, REGION_LABEL[r] ?? r])} onChange={(v) => update({ region: v })} />
            )}
          </fieldset>
        )}

        {!locked.has("school") && facets.school.length > 0 && (
          <fieldset className="fgroup">
            <legend>Near my school</legend>
            <Combobox label="School" name="school" value={f.school} anyLabel="any school"
              options={facets.school.map((x) => [x, schoolNames[x] ?? x])}
              onChange={(v) => update({ school: v, km: v ? f.km : null })} />
            <Combobox label="Distance" name="km" value={String(f.km ?? "")} anyLabel="open to its students"
              options={KM_OPTIONS} onChange={(v) => update({ km: v ? Number(v) : null })} disabled={!f.school} />
          </fieldset>
        )}

        <fieldset className="fgroup">
          <legend>When</legend>
          <Combobox label="Deadline within" name="deadline" value={String(f.deadline ?? "")} anyLabel="any time"
            options={DEADLINE_OPTIONS} onChange={(v) => update({ deadline: v ? Number(v) : null })} />
          <div className="dates">
            <label>From<input type="date" name="from" value={f.from} onChange={(ev) => update({ from: ev.target.value })} /></label>
            <label>To<input type="date" name="to" value={f.to} onChange={(ev) => update({ to: ev.target.value })} /></label>
          </div>
        </fieldset>

        <p className="sidebar-foot">Your filters are saved in this browser for next time.</p>
      </form>
    </div>
  );
}

function CheckGroup({ title, options, selected, counts, onChange }: {
  title: string;
  options: [string, string][];
  selected: string[];
  counts: Record<string, number> | null;
  onChange: (next: string[]) => void;
}) {
  const [all, setAll] = useState(false);
  // Long groups fold, but never hide an option that is ticked.
  const folds = options.length > COLLAPSED + 2;
  const visible = all || !folds ? options : options.filter(([v], i) => i < COLLAPSED || selected.includes(v));
  return (
    <fieldset className="fgroup">
      <legend>{title}</legend>
      <ul className="checks">
        {visible.map(([v, l]) => (
          <li key={v}>
            <label className="check-opt">
              <input
                type="checkbox"
                checked={selected.includes(v)}
                onChange={(ev) => onChange(ev.target.checked ? [...selected, v] : selected.filter((x) => x !== v))}
              />
              <span className="check-label">{l}</span>
              {counts && <span className="count">{counts[v]}</span>}
            </label>
          </li>
        ))}
      </ul>
      {folds && (all || visible.length < options.length) && (
        <button type="button" className="link-button small" onClick={() => setAll((a) => !a)}>
          {all ? "Show fewer" : `Show all ${options.length}`}
        </button>
      )}
    </fieldset>
  );
}

/** Without JavaScript: links to the prebuilt pages for each type, role, region and school. */
export function SidebarFallback({ links }: { links: { title: string; items: [string, string][] }[] }) {
  return (
    <div className="sidebar">
      <div className="sidebar-head"><h2 className="sidebar-title">Browse</h2></div>
      <div className="sidebar-body">
        <p className="hint">
          Filters need JavaScript.{links.some((g) => g.items.length) && " These pages work without it."}
        </p>
        {links.filter((g) => g.items.length).map((g) => (
          <nav key={g.title} className="fgroup" aria-label={g.title}>
            <p className="legend">{g.title}</p>
            <ul className="link-col">
              {g.items.map(([href, text]) => <li key={href}><Link href={href}>{text}</Link></li>)}
            </ul>
          </nav>
        ))}
      </div>
    </div>
  );
}
