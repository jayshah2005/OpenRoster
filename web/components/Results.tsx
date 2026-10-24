"use client";

import { useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import { applyFilters, isEmpty, parseFilters, toQuery } from "@/lib/filter";
import { SITE_URL } from "@/lib/labels";
import { CardList } from "./Card";
import { Icon } from "./Icon";
import { useIndex } from "./useIndex";

/**
 * With no filters in the URL, shows the server-rendered list it was given. With filters, loads the compact
 * index and renders the matching entries, so a shared URL reproduces the same view on any device.
 */
export function Results({ children, baseQuery = "" }: { children: ReactNode; baseQuery?: string }) {
  const params = useSearchParams();
  const merged = new URLSearchParams(baseQuery);
  params.forEach((v, k) => merged.set(k, v));
  const f = parseFilters(merged);
  const active = params.toString() !== "" && !isEmpty(parseFilters(new URLSearchParams(params.toString())));
  const index = useIndex(active);

  if (!active) return <>{children}</>;
  if (!index) return <p className="result-count" aria-live="polite">Loading…</p>;
  const items = applyFilters(index, f, new Date());
  return (
    <>
      <div className="results-bar">
        <p className="result-count" aria-live="polite">
          {items.length} {items.length === 1 ? "match" : "matches"}
        </p>
        <SubscribeLinks query={toQuery(f)} />
      </div>
      <CardList items={items} nowIso={new Date().toISOString()} />
    </>
  );
}

export function SubscribeLinks({ query, staticSlug }: { query?: string; staticSlug?: string }) {
  const ics = staticSlug ? `/feeds/${staticSlug}.ics` : `/api/feed.ics${query ? `?${query}` : ""}`;
  const rss = staticSlug ? `/feeds/${staticSlug}.rss` : `/api/feed.rss${query ? `?${query}` : ""}`;
  return (
    <div className="subscribe" role="group" aria-label="Follow this view">
      <a className="pill-link" href={`${SITE_URL.replace(/^https?:/, "webcal:")}${ics}`}>
        <Icon name="calendar" size={14} /> Subscribe
      </a>
      <a className="pill-link" href={ics}>Calendar (.ics)</a>
      <a className="pill-link" href={rss}><Icon name="rss" size={14} /> RSS</a>
    </div>
  );
}
