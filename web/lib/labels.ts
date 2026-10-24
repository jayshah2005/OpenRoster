export const SITE_NAME = "OpenRoster";
export const REPO_URL = "https://github.com/jayshah2005/OpenRoster";
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "https://openroster.vercel.app").replace(/\/$/, "");
/** Public contact address for takedowns and people without a GitHub account. */
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? "openroster@jayshah.xyz";

export const TYPE_LABEL: Record<string, string> = {
  hackathon: "Hackathon",
  info_session: "Info session",
  tech_talk: "Tech talk",
  career_fair: "Career fair",
  networking: "Networking",
  workshop: "Workshop",
  conference: "Conference",
  case_competition: "Case competition",
  early_career_program: "Early-career program",
  other: "Other",
};

export const TYPE_PLURAL: Record<string, string> = {
  hackathon: "Hackathons",
  info_session: "Info sessions",
  tech_talk: "Tech talks",
  career_fair: "Career fairs",
  networking: "Networking events",
  workshop: "Workshops",
  conference: "Conferences",
  case_competition: "Case competitions",
  early_career_program: "Early-career programs",
  other: "Other events",
};

export const ROLE_LABEL: Record<string, string> = {
  participant: "Attend",
  volunteer: "Volunteer",
  mentor: "Mentor",
  judge: "Judge",
  organizer_team: "Organize",
  workshop_lead: "Lead a workshop",
};

export const MODE_LABEL: Record<string, string> = {
  in_person: "In person",
  online: "Online",
  hybrid: "Hybrid",
  unknown: "Not stated",
};

export const ELIG_LABEL: Record<string, string> = {
  open_to_all: "Open to all",
  school_only: "School only",
  high_school: "High school",
  undergrad: "Undergrad",
  grad: "Grad",
  unknown: "Not stated",
};

export const REGION_LABEL: Record<string, string> = {
  "CA-ON": "Ontario", "CA-QC": "Quebec", "CA-BC": "British Columbia", "CA-AB": "Alberta", "CA-MB": "Manitoba",
  "CA-SK": "Saskatchewan", "CA-NS": "Nova Scotia", "CA-NB": "New Brunswick", "CA-NL": "Newfoundland and Labrador",
  "CA-PE": "Prince Edward Island", "CA-YT": "Yukon", "CA-NT": "Northwest Territories", "CA-NU": "Nunavut",
};

/** Audience tags set by the pipeline's keyword rules (openroster/extract/classify.py), shown as "Who it's for". */
export const AUDIENCE_LABEL: Record<string, string> = {
  first_year: "First-year students",
  second_year: "Second-year students",
  beginner_friendly: "Beginners welcome",
  women_nonbinary: "Women and non-binary students",
  black_students: "Black students",
  indigenous_students: "Indigenous students",
  lgbtq: "2SLGBTQIA+ students",
  high_school: "High-school students",
};

export const COUNTRY_LABEL: Record<string, string> = { CA: "Canada", US: "United States" };

export const ROUTE_LABEL: Record<string, string> = {
  public_link: "Public registration link",
  school_portal_login: "Through your school's career portal (login needed)",
  form: "Online form",
  email: "By email",
  unknown: "See the original page",
};

export const regionName = (r: string | null) => (r ? REGION_LABEL[r] ?? r.split("-")[1] ?? r : "");
