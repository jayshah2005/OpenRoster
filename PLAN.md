# OpenRoster: Plan

Status: **approved 2026-10-23 and built** (owner: "do everything right now", no staged rollout). See §10 for what is done and what is left.
The architecture choices are summarized here. Each one is recorded with its reason in [docs/decisions.md](docs/decisions.md) (D-numbers below).

**Automation principle:** anything that doesn't legally or ethically need you is done by a GitHub Action or a Claude Code agent. Where your judgment is required, it is reduced to **one click on a PR or issue**.

**Change to the spec (your call, 2026-10-23): AI agents are allowed at runtime.** They are an *advisory layer only* (D-020):
- The core pipeline stays rule-based and keeps working with no AI token.
- Agents never fetch the web themselves. They only read content the polite fetcher already stored.
- Agents never publish anything. Their output arrives as PRs or comments that you merge.
- They run through the Claude Code GitHub Action using your Claude subscription token, so no paid API key is needed.

**Hosting change:** Vercel instead of GitHub Pages. The site stays fully static, plus one CDN-cached feed function, so it stays well inside the Hobby free tier (D-022).

## 0. Blanks still to fill in

| Item | Value used in this plan | How it gets filled |
|---|---|---|
| Project name | **OpenRoster** (taken from the folder name) | Change it if you want |
| Home school | **Brock University** | Given |
| Coverage | All of Ontario plus region-independent national sources, **all at once** (see §3a); rest of Canada and US through submissions and discovery | Given |
| GitHub username / repo | `jayshah2005/OpenRoster` | Read from `gh` |
| Bot contact email | `[ ]`, a **new alias you create** (e.g. `openroster.bot@…`) | You tell me once it exists; it stays a placeholder until then, and no fetches run without it |
| Hackathons to seed | `[ ]` | Agents draft the list for every school; you approve or edit it (§9) |

---

## 1. Architecture at a glance

```
config/*.yaml ──► adapters (ICS, Tribe, Localist, JSON-LD, sitemap, HTML, headless, API,
                  hackathon checker, submissions, manual)
                      │  raw candidates + evidence
                      ▼
                normalize → rule-based extraction → confidence ── low ──► needs_review
                      ▼
                dedupe/merge (stable ids, alias map) → validate (JSON Schema)
                      ▼
                data/records/<id>.json   (one file per opportunity, git is the database)
                      ▼
                web/ (Next.js 16, prerendered) → HTML, client index, .ics, RSS → Vercel (static + one cached feed route)
```

| Area | Choice | Short reason |
|---|---|---|
| Language | Python 3.12, one package `openroster` with a CLI (D-001) | Best free tooling for ICS, JSON-LD, HTML and dates. One toolchain for both scraper and site. |
| Schema | Pydantic v2 → exported `schema/opportunity.schema.json` (D-002) | One source of truth, validated in CI |
| Storage | One JSON file per record; past records in `data/archive/<year>/` (D-003) | Reviewable diffs, few conflicts, no database to host |
| HTTP | `httpx` behind one polite fetcher: per-host lock, 2 s spacing, ETag/Last-Modified cache, backoff, page budget, refuses blocked/link-only hosts in code (D-004) | Puts every hard constraint in one place that tests can check |
| robots.txt | `protego` (D-005) | Follows RFC 9309 |
| Parsing | `icalendar`, `recurring-ical-events`, `extruct`, `selectolax`, strict `dateutil` plus my own patterns (D-006) | Free. No fuzzy date guessing. |
| Headless | Playwright, enabled per source only when the audit shows JS-only (D-007) | Free last resort |
| Site | **Next.js 16** in `web/`, every page prerendered (`ensureStatic = "navigation"`), small client components for filters (D-008) | Owner's choice. Works without JS. Measured first load: 190 kB gzipped (budget 300 kB). |
| Hosting | Vercel Hobby, connected to GitHub: `main` deploys to production and each PR gets a preview (D-031, replaces D-022). | Static files are served from the CDN; about 4 data deploys a day, far under the Hobby limits |
| Feeds | Next route handlers `/api/feed.ics` and `/api/feed.rss` return a feed for **any** filter, using the same filter code as the page, with a 6-hour CDN cache. Common feeds are prebuilt as static files (D-009). | Exact live feeds for every filtered view, while cached responses keep function invocations tiny |
| Location | Offline gazetteer (GeoNames `cities15000`, CC-BY, bundled) gives every record lat/lon. School filters are computed by distance from each campus (D-023). | No geocoding API, so no rate limits or terms risk |
| Runtime AI | `anthropics/claude-code-action` with your `CLAUDE_CODE_OAUTH_TOKEN`, with tools restricted (no web, no merge) and a turn and run budget for each job (D-020) | Covers what rules can't do well (review triage, selector repair, summaries) while humans stay the gate |
| Pipeline | Scrape → commit → build → deploy in **one** workflow run (D-010) | Pushes made with `GITHUB_TOKEN` don't trigger other workflows |
| Bot PRs | Opened with `GITHUB_TOKEN`, then CI started on them via `workflow_dispatch`. **No App or PAT needed** (D-011). | `workflow_dispatch` is the documented exception that `GITHUB_TOKEN` *can* trigger. Fallback is a GitHub App if checks don't attach (verified in M3). |
| Keepalive | Monthly API call that re-enables each scheduled workflow (D-012) | Resets the 60-day timer with no dummy commits |
| Quality | ruff, mypy, pytest + fixtures, lychee, axe-core via Playwright (D-013) | Free and runs on CI |

---

## 2. Repository layout

```
openroster/        cli.py fetch.py audit/ adapters/ extract/ pipeline/ hackathons.py model.py ops/
web/               Next.js site: app/ (pages, feed routes), components/, lib/ (filter, feeds), scripts/, e2e/
config/            sources.yaml known_verdicts.yaml schools.yaml hackathons.yaml manual/ also_useful.yaml
data/              records/ archive/ aliases.json review/ health/state.json
reports/           source-audit.md  discovery.md
schema/            opportunity.schema.json
tests/fixtures/    saved responses per adapter (tests never touch the network)
scripts/           bootstrap.sh (one-time repo setup through gh)
.github/           ISSUE_TEMPLATE/ (submit, correct, takedown, add-source, permission-received)
                   workflows/ (see §6)  dependabot.yml
docs/              decisions.md  outreach/  agents.md
TAKEDOWN.md CONTRIBUTING.md CLAUDE.md README.md
```

---

## 3. Data model (summary; the full schema lands in M0)

```yaml
id: "2026-11-ceox1day-north-america-a1b2"    # slug + short hash, stable; merges recorded in aliases.json
type: hackathon | info_session | tech_talk | career_fair | networking | workshop |
      conference | case_competition | early_career_program | other
title, organizer                               # organizer = organization, never a person
roles: [{role: participant|volunteer|mentor|judge|organizer_team|workshop_lead,
         opens, closes, status: upcoming|open|closed|unknown, url, evidence}]
start, end, timezone (IANA), all_day, series_id
mode: in_person | online | hybrid | unknown
location: {venue_name, city, region (ISO 3166-2), country (ISO 3166-1)}
schools: [school_id] | ["open_to_all"]
eligibility: [open_to_all | school_only | high_school | undergrad | grad | unknown]
registration: {route: public_link | school_portal_login | form | email | unknown, url}
cost: {kind: free|paid|unknown, note}   travel_support: {stated, note}
tags, summary (≤200 chars, never copied)
sources: [{url, adapter, source_id, fetched_at}]   obtained_via: [...]
first_seen, last_seen, last_verified
status: scheduled | moved | cancelled | needs_review | past
history: [{at, field, old, new}]   review: {reasons, evidence: [{text, url}]}
```

Also on every record: `geo: {lat, lon, source: gazetteer|venue|manual}` and `near_schools: [{school_id, km}]`, computed at build time.

### 3a. Geography and schools

The question we ask is "**where is the event**", not "which school's site was it on".

- `config/schools.yaml` lists every campus with its city and coordinates, grouped by area.
- **Two school filters:**
  - "**Open to students of X**": eligibility, which covers school-only events.
  - "**Near X**": in-person events within 25 / 50 / 100 km of a campus, plus every online event open to all.
  - Example: Brock + 100 km takes in Niagara, Hamilton and the west GTA.
- **No staged rollout** (owner, 2026-10-23). Every school and source below is researched, audited and built at once. The groups below only set the default distance presets and the order schools appear in lists.

| Group | Area | Schools |
|---|---|---|
| T1 | Niagara | Brock, Niagara College (Welland, NOTL) |
| T2 | Hamilton and the Golden Horseshoe | McMaster, Mohawk, Sheridan, Waterloo, Laurier, Guelph, Conestoga |
| T3 | GTA | UofT (St. George, UTM, UTSC), TMU, York, OCAD, Ontario Tech, Humber, Seneca, Centennial, George Brown, Durham |
| T4 | Rest of Ontario | Western, Fanshawe, Windsor, St. Clair, Queen's, St. Lawrence, Trent, Fleming, uOttawa, Carleton, Algonquin, Laurentian, Lakehead, Nipissing, Algoma, Georgian, Loyalist, Cambrian, Canadore, Confederation, Northern, Sault |
| T5 | Rest of Canada, then US | Added as submissions and sources arrive |

**Region-independent sources** run from day one; their events get located and filtered by distance:
- bank and company student pages (BMO, Scotiabank, RBC, TD, CIBC, Shopify, etc., once audited)
- CEOx1Day and other national programs
- Hack Club
- Luma city calendars for Toronto, Hamilton and Waterloo, only where an official iCal link exists

**Pipeline rules:**
- **No guessed dates:** a date needs an explicit day, month and year (or a year set in source config) plus a known time zone. Otherwise the record becomes `needs_review` with its evidence, and stays hidden until resolved.
- **Dedupe:**
  - Records with the same ICS UID or canonical URL are merged.
  - Otherwise records merge when they share a start date (±1 day) and a city or online mode, and their titles score ≥ 90 on rapidfuzz.
  - Scores of 80–90 go to review.
  - On merge, every source link is kept and source priority decides between conflicting values: manual > submission > feed > HTML > headless.
- **Recurring events:** RRULEs are expanded 120 days ahead with EXDATE and RECURRENCE-ID handled, using the event's TZID, so daylight-saving changes come out right.
- **Cancellations and moves:**
  - Cancelled or moved events get a banner and a `history` entry.
  - An event missing from its only source on 2 consecutive runs goes to review; it is not deleted.
- **Archive:** a record moves to the archive the day after it ends, and its page stays up marked "past".
- **No personal data:** a CI check fails if any record contains an email address, a phone number or a social handle outside the allow-listed contact routes.

---

## 4. Sources and compliance

**`openroster audit <url>`** prints:
- the robots.txt result for our User-Agent
- the terms-of-use URL, with the clauses that match scrape/crawl/robot/automated/republish/commercial quoted
- any known verdict
- the detected platform (Tribe, Localist, ICS links, JSON-LD Event, sitemap, JS-only)
- a provisional verdict

A source runs only when the verdict is `allowed` **and** `reviewed: true`. Only you can set `reviewed`, by merging the PR described in §6.

**Known verdicts:** these are encoded in `known_verdicts.yaml` with their reasons, and blocked hosts are refused in the fetcher code itself.

| Site | Verdict |
|---|---|
| devpost.com (and its subdomains) | blocked |
| mlh.com / mlh.io | permission_required |
| eventbrite.com, linkedin.com, joinhandshake.com, login-walled portals | blocked |
| Luma | official iCal links only |
| Form hosts (Google Forms, Tally, Typeform, Jotform, Microsoft Forms) | link-only |

**Adapters** (all config-driven, all with fixture tests):

| Adapter | What it does |
|---|---|
| `ics` | Club Google Calendars, official Luma iCal links, campus exports |
| `tribe` / `localist` | Public campus calendar read APIs, detected automatically during audit |
| `jsonld` | Pages with schema.org Event data |
| `sitemap` | Finds event pages on allowed sites |
| `html` | Per-source selectors, with a structure fingerprint for health checks. Starts with BMO, Scotiabank and one company hackathon page. |
| `headless` | Same selector config, rendered with Playwright. Last resort only. |
| `hackclub` | Hack Club's public API. Records are tagged `mostly_high_school`. |
| `hackathon_site` | Daily same-domain crawl of each configured hackathon (deadlines move fast), depth ≤ 2 and ≤ 12 pages, with priority keywords. Finds dates, application status and role links with nearby deadlines. Every date keeps its evidence. Newly found role calls go to the daily review PR. |
| `submissions` | Issue forms, validated by an Action |
| `manual` | Curated YAML |

**Risk:** BMO, Scotiabank or the chosen company page may turn out to be JS-only, behind a bot check, or forbidden by terms. If so, I record the verdict, try the next candidate, and report it at M2. I never work around a block.

---

## 5. Website

- **Pages:** list `/`, `/calendar/`, `/o/<id>/`, `/digest/`, `/about/`, `/submit/`, `/takedown/`, `/also-useful/`, plus pre-rendered facet pages (`/type/…`, `/role/…`, `/region/…`, `/school/…`) for no-JS browsing.
- **Without JS:** a paginated HTML list and facet links. The calendar shows as a weekly agenda.
- **With JS:** client components load a compact index (chunked by month once it grows) and handle every filter in the spec. All filter state lives in the query string, so a shared URL gives the same view.
- **Feeds:** every filtered view gets an exact subscribable feed at `/api/feed.ics?<same query>` and `/api/feed.rss?<same query>` from one cached route handler.
  - The function reads the static index from the CDN and is cached for 6 hours, so each distinct filter costs about 4 invocations a day.
  - Common feeds are also prebuilt as static files.
  - If the function is ever disabled, the page falls back to a browser-generated `.ics` snapshot.
- **Opportunity page:**
  - every role with its window and status
  - the event's own time zone, plus your local time when JS runs
  - all source links
  - "last verified on <date>"
  - a prefilled "Report a problem" issue link
  - a single-event .ics
- **Quality, all checked in CI:**
  - mobile-first, keyboard accessible, axe contrast checks
  - dark mode (system setting plus a toggle)
  - no cookies, analytics or third-party requests
  - gzipped first load (HTML + CSS + JS, data excluded) must stay under 300 kB

---

## 6. Automation: GitHub Actions (runtime, free tier, no AI)

| Workflow | Trigger | Automates |
|---|---|---|
| `ci.yml` | push, PR, dispatch | Lint, types, fixture tests, schema validation, PII check, site build, size budget, axe, internal link check |
| `scrape-build-deploy.yml` | every 6 h, dispatch, config/data push | Scrape → pipeline → validate → commit if changed → build → deploy → health → re-verify records whose source was fetched (updates `last_verified`) |
| `audit.yml` | PR or push touching `config/sources.yaml`, daily | Re-audits every source, regenerates `reports/source-audit.md`, and **opens a "Source review" PR per new or changed source** containing the audit, the quoted terms clauses and a sample of the parsed output. Merging it is how you mark the source `reviewed: true`. If a source's robots.txt or terms change later, the source is auto-disabled and a new review PR is opened. |
| `discover.yml` | daily (bounded by page budgets) | Rule-based discovery on **allowed, reviewed** pages only: Google Calendar embeds (→ public ICS URL), official Luma iCal links, Tribe/Localist endpoints, JSON-LD Event pages, and hackathon URLs mentioned in reviewed feeds. Candidates are deduped against config and proposed in one "Discovered sources" PR, which goes through the same audit. |
| `submission.yml` | issue opened/edited | Parses the form, validates it (schema, dates, URL reachable when the host is allowed, duplicate check), comments any errors, then opens a bot PR. Edited issues update the PR. On merge, the record goes live on the next build and the issue is closed with a link to the record. |
| `correction.yml` | "correct" issue | Same flow, producing a minimal diff PR against the existing record |
| `takedown.yml` | takedown issue or `takedown` label | **Hides the record immediately** if the requester's email/URL domain matches the record's organizer domain; otherwise opens a removal PR. Sends an SLA reminder comment at 24 h, escalates at 40 h, and closes the issue after merge. |
| `permission.yml` | "permission received" issue form (e.g. MLH) | Records the grant (date, scope, link to the reply) in `known_verdicts.yaml` through a PR and queues those sources for audit |
| `review.yml` | daily, 07:00 Toronto | One PR, updated in place (no new PR or notification unless something changed), with `needs_review` records, possible duplicates and new volunteer/mentor/judge calls, each with evidence. Editing a YAML value in the PR resolves it. |
| `links.yml` | daily for source links (they are fetched anyway), weekly for Also useful | External link check. Dead source links mark records `needs_review`; dead links on the Also useful page open an issue. |
| `health` (step) | each scrape | One issue per source for: fetch errors, zero results after previous results, a structure fingerprint change, or a robots change. The issue includes **rule-based selector suggestions** (the new DOM paths with the highest count of date-like repeated items). It auto-closes after 2 healthy runs. |
| `keepalive.yml` | monthly | Re-enables every scheduled workflow through the API |
| `bootstrap-labels` (step in CI) | first run | Creates or updates labels from `.github/labels.yml` |
| Dependabot + `automerge.yml` | weekly | Patch/minor dependency updates auto-merge when CI is green |
| `digest` (build step) | each build | `/digest/<week>/` page + RSS |

### 6a. Runtime AI jobs (advisory; `claude-code-action`, D-020)

**Guardrails on every job:**
- Allowed tools are limited to reading the repo, running `openroster` CLI commands and editing files on its own branch. No WebFetch, WebSearch or merge rights.
- The job reads scraped text only as quoted data, and the prompt treats that text as untrusted.
- `--max-turns` and a daily run budget cap each job.
- If `CLAUDE_CODE_OAUTH_TOKEN` is missing, the job is skipped, not failed.

| Job | Trigger | What the agent does | Your gate |
|---|---|---|---|
| Review triage | daily review PR | For each `needs_review` item, proposes a resolved date/role/type **with the exact evidence span it relied on**, or leaves it marked unresolvable. Proposals are labelled `extracted_by: ai_suggested`. | You merge the PR |
| Selector repair | `[health]` issue for an HTML source | Uses the fresh snapshot the fetcher stored, writes new selectors, captures a new fixture and runs the adapter tests until they pass, then opens a PR | You merge |
| Submission assist | submission issue that passed validation | Suggests type, roles, eligibility and tags; writes a ≤200-char summary in original words; flags likely duplicates | You merge the bot PR |
| Terms summary | source-review PR | Summarises the stored terms page in plain language, quotes the clauses that matter and recommends a verdict | You merge (the human sign-off the spec requires) |
| Discovery assist | discovered-sources PR | Ranks candidates by relevance (CS/student focus, distance from Ontario campuses) and drops noise | You merge |
| `@claude` | comments by repo owners or members only | General maintenance help on issues and PRs | You merge |

**One-time repo setup is scripted too (`scripts/bootstrap.sh`, run by me through your `gh` login):**
- creates the public repo and pushes
- sets Actions to read/write, with "allow Actions to create PRs"
- links the Vercel project (`vercel link`) and stores `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` as secrets
- sets branch protection that requires `ci`
- turns on Dependabot, creates labels, and sets the description and topics

---

## 7. Automation: Claude Code agents while building (see `docs/agents.md`)

| When | Agents | Output for you to approve |
|---|---|---|
| M0 | Research agents covering all ~40 schools in parallel | Each school's calendar platform (Tribe/Localist/ICS/none), public club calendar links (CS, engineering, business and tech clubs), career-centre event pages, the school's hackathons with official URLs, and campus coordinates → draft `config/schools.yaml`, `config/hackathons.yaml` and a sources draft. These come from targeted searches, not from scraping a directory. |
| M0 | Research agent for region-independent sources | Student and early-career event pages of Canadian banks, Big 4 firms and tech companies; national programs (CEOx1Day, etc.); Luma city iCal links → a sources draft |
| M0 | 1 terms-reading agent per candidate source | A plain-language summary of each site's terms with exact quotes, attached to its audit entry, so your review takes seconds |
| M1–M2 | 1 builder agent per adapter, each in its own git worktree | Adapter + saved fixtures + tests, merged by me after CI passes |
| M2 | Fixture-capture agent | Fetches one polite sample per approved source (through the polite fetcher) and stores it as a fixture |
| M3 | Outreach agent | Personalised draft emails (MLH, each club, each career centre, BMO/Scotiabank if refused) in `docs/outreach/`, with `mailto:` links ready to send |
| Before each review stop | Review agent | `/code-review` of the milestone diff and an acceptance-check run, with results attached to the milestone summary |
| M6 | Docs agent | README, CONTRIBUTING, TAKEDOWN and CLAUDE.md, checked against the actual commands |

---

## 8. Milestones

- **M0: foundation.** Package skeleton, schema, config formats, polite fetcher with tests, known verdicts, CI, bootstrap script; research agents produce the draft school, hackathon and source lists.
- **M1: structured adapters + audit.** ICS, Tribe, Localist, JSON-LD, sitemap and Hack Club adapters; extraction, dedupe and archive; `openroster audit` (**AC1**); `audit.yml` with review PRs.
- **M2: HTML + audit report.** HTML and headless adapters; BMO, Scotiabank and one company hackathon page (or documented refusals); `reports/source-audit.md` (**AC2**). **⏸ Stop for your review.**
- **M3: hackathons + submissions.** Hackathon site checker; issue forms; submission, correction, takedown and permission workflows; outreach drafts; bot-PR CI verified (D-011).
- **M4: website.** All views, filters in the URL, distance filters, the Edge feed function, no-JS mode, dark mode, budgets; deployed to Vercel with ≥ 3 source types (**AC3**, **AC4**, **AC6**). **⏸ Stop for your review.**
- **M5: operations.** Review PR, discovery, digest, health with selector suggestions, link checks, keepalive, Dependabot auto-merge (**AC5**), plus all the §6a AI jobs, each shown working once on a real issue or PR.
- **M6: docs.** README, CONTRIBUTING, TAKEDOWN, CLAUDE.md, agents.md, Also useful.

**How I'll show each acceptance check:**

| # | Evidence |
|---|---|
| AC1 | `openroster audit` output for an allowed site, devpost, mlh, eventbrite and a Google Form |
| AC2 | The report, plus a test that every configured source appears in it |
| AC3 | Live Vercel URL; the build log counts records by `obtained_via` |
| AC4 | A Playwright test loads the same query string in a fresh browser context; you check it on your phone |
| AC5 | A PR with a corrupted fixture (CI goes red); a dispatch run against an empty fixture opens a `[health]` issue |
| AC6 | A test issue → bot PR → merge → record live |

---

## 9. What is still yours (the minimum)

| # | Task | Why it can't be automated | Effort |
|---|---|---|---|
| 1 | Create the bot email alias and tell me; confirm the project name | Only you can create it | 5 min |
| 2 | Run `! gh auth login` and `! vercel login` once, then OK the bootstrap script | It acts on your GitHub and Vercel accounts and creates a public repo | 3 min |
| 3 | Run `claude setup-token` and add the result as the `CLAUDE_CODE_OAUTH_TOKEN` repo secret (or let the bootstrap script store it with `gh secret set`) | It's your subscription credential | 2 min |
| 4 | Create a Vercel token and store it as `VERCEL_TOKEN` (the bootstrap script prompts for it) | Account credential | 2 min |
| 5 | Skim `docs/decisions.md` and flag anything you disagree with | Product judgment | 5 min |
| 6 | Merge "Source review" PRs (one batch PR for the initial research, then one per new source) | The spec requires your sign-off on each source; AI terms summaries are attached | ~30 s per source |
| 7 | Confirm the agent-drafted hackathon list (add or remove names) | The spec says the seed list comes from you | 10 min, once |
| 8 | Send the drafted emails (MLH, clubs, career centres) and file a "permission received" issue for any yes | They go out under your name to outside parties | 15 min, once |
| 9 | Merge submission PRs, AI repair PRs and the daily review PR | Editorial judgment; everything is pre-validated | a few min/week |
| 10 | Handle takedowns the bot can't auto-verify | Abuse protection | rare |

---

## 10. Status (2026-10-24)

Live at https://github.com/jayshah2005/OpenRoster. CI is green: 103 Python tests, 11 web unit tests, 18 browser and
accessibility tests, the size budget and the link check.

**Verified on GitHub Actions:**
- The first full audit covered 178 sources and hackathon sites in about 4 minutes, running sites in parallel with one worker per host. 152 were allowed and 25 blocked by robots.txt, terms or a known verdict.
- Update data (scrape, validate, LISTINGS.md, health), Daily review, Link check, Keepalive and Maintenance all run successfully.
- Weekly discovery found 5 feeds on its first run.
- Vercel deploys `main` and PR previews through its GitHub app; no token needed.

**Added since the first build:**
- **Discovery and selectors:** weekly discovery (rule-based, plus an optional search-only agent), and rule-based selector proposals for HTML sources.
- **New listing features:** audience and year-of-study tags, an "open for applications now" filter, and "Apply by" reminders in every calendar feed.
- **New site pages:** LISTINGS.md for GitHub, a programs directory, a start guide for early-career students, contribute and data pages, and a Google Calendar link on each listing.
- **Engine fixes:** parsing for noon and 24-hour times, fuller summaries, Engage RSS detection, and dates read from JavaScript-rendered hackathon sites.
- **Hardening:** one failing site no longer stops an audit or scrape, Google Calendar feeds are blocked because Google's robots.txt disallows them, and the commit convention is enforced by a hook.

**Waiting on the owner:**
1. Settings → Actions → General → allow GitHub Actions to create and approve pull requests. Every bot PR needs this.
2. A Vercel token (`VERCEL_TOKEN` secret) or the Vercel GitHub app, to deploy.
3. Merging the Source review PR, which approves 93 sources.
4. Optionally, the `CLAUDE_CODE_OAUTH_TOKEN` secret for the AI helpers and the discovery agent.
