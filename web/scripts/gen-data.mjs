// Prebuild: turn the pipeline's output (../data, ../config) into JSON modules the app imports, plus the
// compact client index in public/data/. Runs before `next build` and `next dev`.
import { mkdirSync, readFileSync, readdirSync, existsSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const web = join(dirname(fileURLToPath(import.meta.url)), "..");
const root = join(web, "..");
const dataDir = process.env.OPENROSTER_DATA ?? join(root, "data");
const gen = join(web, "generated");
const pub = join(web, "public", "data");
mkdirSync(gen, { recursive: true });
mkdirSync(pub, { recursive: true });

function readJsonDir(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .sort()
    .map((f) => JSON.parse(readFileSync(join(dir, f), "utf8")));
}

function readYaml(path, key) {
  if (!existsSync(path)) return [];
  return parse(readFileSync(path, "utf8"))?.[key] ?? [];
}

const records = readJsonDir(join(dataDir, "records")).filter((r) => r.status !== "needs_review");
const archiveDir = join(dataDir, "archive");
const archive = existsSync(archiveDir)
  ? readdirSync(archiveDir).flatMap((y) => readJsonDir(join(archiveDir, y)))
  : [];
const schools = readYaml(join(root, "config", "schools.yaml"), "schools").map((s) => ({
  id: s.id,
  name: s.name,
  campuses: (s.campuses ?? []).map((c) => ({ name: c.name ?? "", city: c.city ?? null })),
}));
const alsoUseful = readYaml(join(root, "config", "also_useful.yaml"), "links");
const programs = readYaml(join(root, "config", "programs.yaml"), "programs");

// Status page data: what is configured, approved and audited, and what the last run produced.
const sourceFiles = existsSync(join(root, "config", "sources"))
  ? readdirSync(join(root, "config", "sources")).filter((f) => f.endsWith(".yaml"))
  : [];
const sources = sourceFiles.flatMap((f) => readYaml(join(root, "config", "sources", f), "sources"));
const auditDir = join(dataDir, "audit");
const audits = existsSync(auditDir) ? readJsonDir(auditDir) : [];
const verdicts = audits.reduce((acc, a) => ({ ...acc, [a.verdict]: (acc[a.verdict] ?? 0) + 1 }), {});
const statePath = join(dataDir, "health", "state.json");
const state = existsSync(statePath) ? JSON.parse(readFileSync(statePath, "utf8")) : {};
const status = {
  configured: sources.length,
  approved: sources.filter((s) => s.reviewed === true).length,
  enabled: sources.filter((s) => s.enabled !== false).length,
  audited: audits.length,
  verdicts,
  lastRun: state.pipeline ?? null,
  failing: Object.entries(state.sources ?? {})
    .filter(([, s]) => s && s.ok === false)
    .map(([id, s]) => ({ id, error: String(s.error ?? "").slice(0, 160) })),
};

// Compact entry: everything the list, filters and feeds need, without history or evidence.
const compact = (o) => ({
  id: o.id,
  type: o.type,
  title: o.title,
  organizer: o.organizer,
  roles: o.roles.map((r) => ({ role: r.role, opens: r.opens, closes: r.closes, status: r.status, url: r.url })),
  start: o.start,
  end: o.end,
  timezone: o.timezone,
  all_day: o.all_day,
  mode: o.mode,
  city: o.location.city,
  region: o.location.region,
  country: o.location.country,
  schools: o.schools,
  near: o.near_schools.map((n) => [n.school_id, n.km]),
  eligibility: o.eligibility,
  cost: o.cost.kind,
  tags: o.tags,
  summary: o.summary,
  status: o.status,
  url: o.registration.url ?? o.sources[0].url,
  first_seen: o.first_seen,
  last_verified: o.last_verified,
});

const index = records.map(compact);
const built = new Date().toISOString();
writeFileSync(join(gen, "records.json"), JSON.stringify(records));
writeFileSync(join(gen, "archive.json"), JSON.stringify(archive));
writeFileSync(join(gen, "index.json"), JSON.stringify(index));
writeFileSync(join(gen, "schools.json"), JSON.stringify(schools));
writeFileSync(join(gen, "also-useful.json"), JSON.stringify(alsoUseful));
writeFileSync(join(gen, "programs.json"), JSON.stringify(programs));
writeFileSync(join(gen, "status.json"), JSON.stringify(status));
writeFileSync(join(gen, "meta.json"), JSON.stringify({ built, count: index.length }));

// Client index: one file while small, split by month once large so the first load stays light.
const chunks = [];
if (index.length > 1500) {
  const byMonth = Object.groupBy(index, (e) => e.start.slice(0, 7));
  for (const [month, items] of Object.entries(byMonth).sort()) {
    writeFileSync(join(pub, `index-${month}.json`), JSON.stringify(items));
    chunks.push(`index-${month}.json`);
  }
} else {
  writeFileSync(join(pub, "index.json"), JSON.stringify(index));
  chunks.push("index.json");
}
writeFileSync(join(pub, "meta.json"), JSON.stringify({ built, count: index.length, chunks }));
console.log(`gen-data: ${records.length} live, ${archive.length} archived, ${schools.length} schools`);
