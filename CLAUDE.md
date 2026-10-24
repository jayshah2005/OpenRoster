# OpenRoster: notes for Claude

Open-source tracker of opportunities for CS students. The Python pipeline (`openroster/`) writes
`data/records/*.json`. The Next.js site (`web/`) reads that data at build time and deploys to Vercel.

## Commands

```bash
uv sync
uv run pytest -q                              # all adapters on saved fixtures; never hits the network
uv run ruff check openroster tests scripts && uv run mypy openroster
uv run openroster audit <url>                 # verdict + reasons; --all audits every source
uv run openroster scrape [--only <ids>]       # runs only reviewed + allowed sources
uv run openroster validate                    # JSON Schema + no-personal-data check on data/
uv run openroster schema                      # re-export schema/opportunity.schema.json after model changes
uv run openroster review                      # daily review report + fill-in stubs
uv run openroster suggest-selectors <id> --html <file>
uv run openroster submission --kind submit|correct|takedown|permission --body <file> [--write]
OPENROSTER_DATA=/tmp/p uv run python scripts/preview_from_fixtures.py   # preview data, no network

cd web
npm run dev | npm run build                   # prebuild runs scripts/gen-data.mjs (reads ../data, ../config)
npm run lint && npm run typecheck && npm test
npm run e2e                                   # Playwright: AC4, no-JS, axe (needs `next start -p 3123`)
npm run check-size && npm run check-links
```

`web/` is Next.js 16 with Cache Components. Read `web/node_modules/next/dist/docs/` before changing Next
code: APIs differ from older versions. The root layout sets `ensureStatic = "navigation"`, so every page must
stay static. The only request-time code is `app/api/feed.{ics,rss}`, which is CDN-cached for 6 hours.

## Git

Before any commit or new branch, load the `commit-convention` skill (`.claude/skills/commit-convention/SKILL.md`)
and follow it: `type[/scope]: summary` with types feat/fix/refactor/chore and scopes from its allowlist. Only commit
or push when the user asks. A PreToolUse hook (`.claude/hooks/check_git_convention.py`) blocks anything else.

## Hard rules (never break, never weaken)

- **Free only.** No paid APIs or hosting. The scraper and site use no AI. AI jobs (`.github/workflows/ai.yml`, `discover.yml`) are advisory: they never fetch web pages (the weekly discovery agent may use web *search*), never merge, and their output is a PR or comment that a person merges.
- **Fetching.** All network access goes through `openroster/fetch.py`:
  - honest User-Agent with the repo URL and contact address
  - ≥ 2 s per host, or robots.txt Crawl-delay if longer, with no parallel requests to one host
  - robots.txt checked on every URL and every redirect
  - conditional requests, backoff, and a page budget per source
- **No workarounds.** Never bypass logins, CAPTCHAs, bot checks or rate limits, and never disguise the bot.
- **Source sign-off.** A source runs only when its latest audit says `allowed` **and** the owner set `reviewed: true` (by merging the Source review PR). Never set `reviewed: true` yourself.
- **Known verdicts** (`config/known_verdicts.yaml`, enforced in code):

  | Site | Verdict |
  |---|---|
  | devpost.com | blocked |
  | mlh.io / mlh.com | permission_required (no fetches until permission is recorded) |
  | eventbrite, linkedin.com, joinhandshake.com, login portals | blocked |
  | Luma | official iCal links (`api.lu.ma/ics/get`) only, never JSON endpoints |
  | Google Forms, Tally, Typeform, Jotform, MS Forms | link-only |

- **Stored data.** Facts only: title, organizer, dates, location, mode, eligibility, roles and deadlines, plus a summary of at most 200 characters in our own words. Always link to the original. Copy no descriptions, images or logos.
- **No personal data.** No attendee, speaker, organizer or volunteer names, emails or photos. Speaker names are stripped from titles.
- **Dates.** Extraction is rule-based. A date that can't be read with confidence is never guessed: the item becomes `needs_review` with its evidence and goes into the daily review PR.
- **Takedowns.** Removal within 48 hours. `data/takedowns.json` entries are never republished.

## Layout

- `config/sources/*.yaml`: sources.
  - Research-generated files come from `scripts/research_to_config.py`, which keeps entries marked `hand_tuned: true`.
  - `tuned-feeds.yaml` is hand-written.
- `config/hackathons.yaml`, `config/schools.yaml`, `config/manual/`, `config/submissions/`, `config/overrides.yaml`.
- `data/records/` (live), `data/archive/<year>/`, `data/audit/` (latest audit per source), `data/health/state.json`.
- `tests/fixtures/`: saved responses, one per adapter. `tests/fixtures/sources/<id>.html` must parse with that source's selectors.
