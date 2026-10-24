// Mirrors schema/opportunity.schema.json (exported from openroster/model.py).

export type OppType =
  | "hackathon" | "info_session" | "tech_talk" | "career_fair" | "networking" | "workshop"
  | "conference" | "case_competition" | "early_career_program" | "other";
export type Role = "participant" | "volunteer" | "mentor" | "judge" | "organizer_team" | "workshop_lead";
export type RoleStatus = "upcoming" | "open" | "closed" | "unknown";
export type Mode = "in_person" | "online" | "hybrid" | "unknown";
export type Eligibility = "open_to_all" | "school_only" | "high_school" | "undergrad" | "grad" | "unknown";
export type Status = "scheduled" | "moved" | "cancelled" | "needs_review" | "past";

export interface RoleWindow {
  role: Role;
  opens: string | null;
  closes: string | null;
  status: RoleStatus;
  url: string | null;
  evidence?: string | null;
}

export interface Opportunity {
  id: string;
  type: OppType;
  title: string;
  organizer: string;
  roles: RoleWindow[];
  start: string;
  end: string | null;
  timezone: string;
  all_day: boolean;
  series_id: string | null;
  mode: Mode;
  location: { venue_name: string | null; city: string | null; region: string | null; country: string | null };
  geo: { lat: number; lon: number; source: string } | null;
  near_schools: { school_id: string; km: number }[];
  schools: string[];
  eligibility: Eligibility[];
  registration: { route: string; url: string | null };
  cost: { kind: "free" | "paid" | "unknown"; note: string | null };
  travel_support: { stated: boolean; note: string | null };
  tags: string[];
  summary: string;
  sources: { url: string; adapter: string; source_id: string; fetched_at: string }[];
  obtained_via: string[];
  first_seen: string;
  last_seen: string;
  last_verified: string;
  status: Status;
  history: { at: string; field: string; old: string | null; new: string | null }[];
}

/** Compact entry used by the client index, filters and feeds (see scripts/gen-data.mjs). */
export interface Entry {
  id: string;
  type: OppType;
  title: string;
  organizer: string;
  roles: Omit<RoleWindow, "evidence">[];
  start: string;
  end: string | null;
  timezone: string;
  all_day: boolean;
  mode: Mode;
  city: string | null;
  region: string | null;
  country: string | null;
  schools: string[];
  near: [string, number][];
  eligibility: Eligibility[];
  cost: "free" | "paid" | "unknown";
  tags: string[];
  summary: string;
  status: Status;
  url: string;
  first_seen: string;
  last_verified: string;
}

export interface School {
  id: string;
  name: string;
  campuses: { name: string; city: string | null }[];
}

export interface Link {
  name: string;
  url: string;
  description: string;
}

/** A recurring early-career program from config/programs.yaml. Dates change yearly, so it links out. */
export interface Program {
  name: string;
  organization: string | null;
  url: string;
  kind: string;
  timing: string | null;
  who: string;
  /** Years of study it targets; 0 means high school. Empty when the program does not say. */
  years: number[];
  link_only: boolean;
  notes: string | null;
  checked: string;
}
