// Prebuilt (static) feeds: all, each type/role/region/school, type×role and role×region.
// Any other filter combination is served by /api/feed.{ics,rss}, which shares lib/filter.ts.
import { facets, liveEntries, meta } from "./data";
import { selectFacet } from "./facetPages";
import type { Entry } from "./types";

export function prebuiltFeeds(): Map<string, Entry[]> {
  const fx = facets();
  const built = new Date(meta.built).getTime();
  const since = (days: number) => new Date(built - days * 86_400_000).toISOString();
  const feeds = new Map<string, Entry[]>([
    ["all", liveEntries],
    ["digest", liveEntries.filter((e) => e.first_seen >= since(7))],
    ["new-today", liveEntries.filter((e) => e.first_seen >= since(1))],
  ]);
  for (const t of fx.type) feeds.set(`type-${t}`, selectFacet("type", t));
  for (const r of fx.role) feeds.set(`role-${r}`, selectFacet("role", r));
  for (const rg of fx.region) feeds.set(`region-${rg}`, selectFacet("region", rg));
  for (const s of fx.school) feeds.set(`school-${s}`, selectFacet("school", s));
  for (const t of fx.type) {
    for (const r of fx.role) {
      const sel = feeds.get(`type-${t}`)!.filter((e) => e.roles.some((x) => x.role === r));
      if (sel.length) feeds.set(`type-${t}--role-${r}`, sel);
    }
  }
  for (const r of fx.role) {
    for (const rg of fx.region) {
      const sel = feeds.get(`role-${r}`)!.filter((e) => e.region === rg);
      if (sel.length) feeds.set(`role-${r}--region-${rg}`, sel);
    }
  }
  return feeds;
}
