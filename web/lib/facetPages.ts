import { facets, liveEntries, schoolById } from "./data";
import { REGION_LABEL, ROLE_LABEL, TYPE_PLURAL } from "./labels";
import type { Entry } from "./types";

export type FacetKind = "type" | "role" | "region" | "school";

/** "Near or open to" for schools uses 50 km, matching the prebuilt school feeds. */
export const SCHOOL_KM = 50;

export function selectFacet(kind: FacetKind, value: string): Entry[] {
  switch (kind) {
    case "type":
      return liveEntries.filter((e) => e.type === value);
    case "role":
      return liveEntries.filter((e) => e.roles.some((r) => r.role === value));
    case "region":
      return liveEntries.filter((e) => e.region === value);
    case "school":
      return liveEntries.filter(
        (e) => e.schools.includes(value) || e.near.some(([s, km]) => s === value && km <= SCHOOL_KM),
      );
  }
}

export function facetTitle(kind: FacetKind, value: string): string {
  switch (kind) {
    case "type":
      return TYPE_PLURAL[value] ?? value;
    case "role":
      return value === "participant" ? "Events to attend" : `${ROLE_LABEL[value] ?? value} opportunities`;
    case "region":
      return `Opportunities in ${REGION_LABEL[value] ?? value}`;
    case "school":
      return `Near or open to ${schoolById.get(value)?.name ?? value}`;
  }
}

export function facetValues(kind: FacetKind): string[] {
  const values = facets()[kind];
  // ensureStatic requires at least one param set even before any data exists.
  return values.length ? values : [kind === "type" ? "hackathon" : kind === "role" ? "participant" : kind === "region" ? "CA-ON" : "brock"];
}

export function baseQueryFor(kind: FacetKind, value: string): string {
  if (kind === "school") return `school=${value}&km=${SCHOOL_KM}`;
  return `${kind}=${encodeURIComponent(value)}`;
}
