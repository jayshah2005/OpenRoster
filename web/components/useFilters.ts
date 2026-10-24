"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Sort } from "@/lib/directory";
import { type Filters, isEmpty, parseFilters, toQuery } from "@/lib/filter";

const PREFS_KEY = "or-filters";
const SORTS: Sort[] = ["deadline", "start", "new"];

function readPrefs(): string {
  try {
    return localStorage.getItem(PREFS_KEY) ?? "";
  } catch {
    return ""; // storage blocked (private mode, disabled site data): filters still work, they just aren't remembered
  }
}

function writePrefs(qs: string) {
  try {
    if (qs) localStorage.setItem(PREFS_KEY, qs);
    else localStorage.removeItem(PREFS_KEY);
  } catch {
    // see readPrefs
  }
}

/**
 * Filter state for a page. The URL is the source of truth, so every view can be shared. `baseQuery` is the
 * page's fixed filter (e.g. type=hackathon on /type/hackathon/): it applies underneath and its keys are locked.
 */
export function useFilters(baseQuery = "") {
  const router = useRouter();
  const pathname = usePathname();
  const urlQs = useSearchParams().toString();
  // A click shows its result at once; the URL catches up a moment later (router.replace is async). The
  // optimistic copy is dropped as soon as the URL changes, whether from our update or the back button.
  const [optimistic, setOptimistic] = useState<{ qs: string; from: string } | null>(null);
  if (optimistic && optimistic.from !== urlQs) setOptimistic(null);
  const qs = optimistic && optimistic.from === urlQs ? optimistic.qs : urlQs;
  const own = useMemo(() => parseFilters(new URLSearchParams(qs)), [qs]);
  const f = useMemo(() => {
    const merged = new URLSearchParams(baseQuery);
    new URLSearchParams(qs).forEach((v, k) => merged.set(k, v));
    return parseFilters(merged);
  }, [qs, baseQuery]);
  const locked = useMemo(() => new Set(new URLSearchParams(baseQuery).keys()), [baseQuery]);
  const sortParam = new URLSearchParams(qs).get("sort") as Sort | null;
  const sort: Sort = sortParam && SORTS.includes(sortParam) ? sortParam : "deadline";

  function go(filters: Filters, nextSort: Sort) {
    const p = new URLSearchParams(toQuery(filters));
    if (nextSort !== "deadline") p.set("sort", nextSort);
    const s = p.toString();
    // Remember what the visitor picked (not the search text) for their next visit. Only their own changes are
    // saved: opening a link someone shared shows that view without replacing their preferences.
    const saved = new URLSearchParams(p);
    saved.delete("q");
    writePrefs(saved.toString());
    setOptimistic({ qs: s, from: urlQs });
    router.replace(s ? `${pathname}?${s}` : pathname, { scroll: false });
  }

  return {
    f,
    own,
    locked,
    sort,
    active: !isEmpty(own),
    update: (patch: Partial<Filters>) => go({ ...own, ...patch }, sort),
    setSort: (s: Sort) => go(own, s),
    clear: () => go(parseFilters(new URLSearchParams()), sort),
  };
}

/**
 * Brings back the visitor's saved filters (see `go` above) when they open a page with no filters in the URL; a
 * shared link always wins. Returns true while the restored view is showing, so the page can say so.
 */
export function useSavedFilters(baseQuery = ""): boolean {
  const router = useRouter();
  const pathname = usePathname();
  const qs = useSearchParams().toString();
  const [restoredQs, setRestoredQs] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    if (qs) return;
    const locked = new Set(new URLSearchParams(baseQuery).keys());
    const saved = new URLSearchParams(readPrefs());
    for (const k of [...saved.keys()]) if (locked.has(k) || k === "q") saved.delete(k);
    const s = saved.toString();
    if (!s) return;
    router.replace(`${pathname}?${s}`, { scroll: false });
    void Promise.resolve().then(() => setRestoredQs(s)); // after this effect, not during it
  }, [qs, baseQuery, pathname, router]);

  // The note goes away as soon as the visitor changes anything.
  return restoredQs !== null && qs === restoredQs;
}
