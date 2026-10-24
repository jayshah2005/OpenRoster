"use client";

import { type ChangeEvent, type ReactNode, useMemo, useRef, useState } from "react";
import { type Item, SORT_LABEL, type Sort, itemMatches, sortItems } from "@/lib/directory";
import { toQuery } from "@/lib/filter";
import type { Program } from "@/lib/types";
import { Card, ProgramCard } from "./Card";
import { Combobox } from "./Combobox";
import { Icon } from "./Icon";
import { SubscribeLinks } from "./Results";
import { useFilters } from "./useFilters";
import { useIndex } from "./useIndex";

const STEP = 50;

type Props = {
  programs: Program[];
  baseQuery?: string;
  feedSlug: string;
  /** Shown above the list when there are no dated listings at all (e.g. the pipeline's red flags). */
  notice?: ReactNode;
  /** The server-rendered list, shown until the index has loaded. */
  children: ReactNode;
};

/** The main column: search, sort, count, feed links and the combined list of events and programs. */
export function Directory({ programs, baseQuery = "", feedSlug, notice, children }: Props) {
  const { f, own, active, sort, update, setSort, clear } = useFilters(baseQuery);
  const index = useIndex(true);
  const [limit, setLimit] = useState(STEP);
  const [q, setQ] = useState(f.q);
  const [urlQ, setUrlQ] = useState(f.q);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const now = useMemo(() => new Date(), []);

  const [seen, setSeen] = useState(`${toQuery(f)}|${sort}`);

  // Follow the URL when the search term changes from outside the box (back button, "Clear all").
  if (f.q !== urlQ) {
    setUrlQ(f.q);
    setQ(f.q);
  }
  // New filters or a new order start again from the top of the list.
  if (`${toQuery(f)}|${sort}` !== seen) {
    setSeen(`${toQuery(f)}|${sort}`);
    setLimit(STEP);
  }

  const results = useMemo(() => {
    if (!index) return null;
    const all: Item[] = [
      ...index.map((e) => ({ kind: "event" as const, e })),
      ...programs.map((p) => ({ kind: "program" as const, p })),
    ];
    return sortItems(all.filter((it) => itemMatches(it, f, now)), sort, now);
  }, [index, programs, f, sort, now]);

  function onSearch(ev: ChangeEvent<HTMLInputElement>) {
    const v = ev.target.value;
    setQ(v);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => update({ q: v }), 250);
  }

  const search = (
    <form className="searchbar" role="search" aria-label="Search opportunities" onSubmit={(ev) => { ev.preventDefault(); update({ q }); }}>
      <label className="search-field">
        <span className="sr-only">Search</span>
        <Icon name="search" size={18} />
        <input type="search" name="q" value={q} onChange={onSearch} placeholder="Search hackathons, companies, schools…" autoComplete="off" />
      </label>
      <div className="sort">
        <Combobox label="Sort" name="sort" value={sort === "deadline" ? "" : sort} anyLabel={SORT_LABEL.deadline}
          options={(["start", "new"] as Sort[]).map((s) => [s, SORT_LABEL[s]])}
          onChange={(v) => setSort((v || "deadline") as Sort)} />
      </div>
    </form>
  );

  if (!results) return <>{search}{children}</>;

  const events = results.filter((r) => r.kind === "event").length;
  const shown = results.slice(0, limit);
  const firstProgram = shown.findIndex((r) => r.kind === "program");
  const query = toQuery(f);

  return (
    <>
      {search}
      <div className="results-bar">
        <p className="result-count" aria-live="polite">
          {results.length} {results.length === 1 ? "result" : "results"}
          {events > 0 && results.length > events && <span className="muted"> · {events} events, {results.length - events} programs</span>}
        </p>
        {events > 0 && (active ? <SubscribeLinks query={query} /> : <SubscribeLinks staticSlug={feedSlug} />)}
      </div>
      {index && index.length === 0 && notice}
      {results.length === 0 ? (
        <div className="empty">
          <p className="empty-title">Nothing matches these filters.</p>
          <p>
            {own.q ? <>Try a shorter search, or </> : <>Try </>}
            <button type="button" className="link-button" onClick={clear}>clearing the filters</button>.
          </p>
        </div>
      ) : (
        <ul className="cards">
          {shown.map((r, i) => (
            <ItemRow key={r.kind === "event" ? r.e.id : `p-${r.p.url}-${r.p.name}`} item={r} nowIso={now.toISOString()}
              divider={i === firstProgram && i > 0} />
          ))}
        </ul>
      )}
      {results.length > limit && (
        <div className="more">
          <button type="button" className="button button-quiet" onClick={() => setLimit((l) => l + STEP)}>
            Show more ({results.length - limit} left)
          </button>
        </div>
      )}
    </>
  );
}

function ItemRow({ item, nowIso, divider }: { item: Item; nowIso: string; divider: boolean }) {
  const row = item.kind === "event" ? <Card e={item.e} nowIso={nowIso} /> : <ProgramCard p={item.p} />;
  if (!divider) return row;
  return (
    <>
      <li className="list-divider"><span>Recurring programs, open every year</span></li>
      {row}
    </>
  );
}
