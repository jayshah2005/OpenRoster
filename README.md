# OpenRoster

Hackathons, info sessions, tech talks, career fairs, workshops, case competitions and early-career programs for computer science students, plus volunteer, mentor and judge calls, in one place you can filter. It covers Ontario first, then the rest of Canada and the US.

Event sites like Eventbrite and Luma miss things like bank info sessions, CEOx1Day-style programs, company-run student hackathons and volunteer calls posted on a hackathon's own site. OpenRoster collects these from public calendars, campus APIs, company pages, hackathon sites and community submissions. Everything runs on free tiers with no paid APIs.

**Site:** https://openroster.vercel.app · **Submit something:** [open the form](../../issues/new?template=submit-opportunity.yml)

## How it works

```
config/            sources (audited + owner-approved), schools, hackathons, curated programs
   │
openroster/        Python: polite fetcher → adapters → rule-based extraction → dedupe/merge → data/records/*.json
   │               (GitHub Actions, every 6 hours; commits only when data changes)
data/              one JSON file per opportunity; git is the database
   │
web/               Next.js: static pages + one cached feed route, deployed to Vercel
```

| Part | What it does |
|---|---|
| `openroster/fetch.py` | All network access. Uses an honest User-Agent, waits 2 s per host (or the site's Crawl-delay), follows robots.txt, makes conditional requests, backs off on errors, has a page budget, and refuses blocked hosts in code. |
| `openroster/adapters/` | iCal, WordPress Events Calendar, Localist, JSON-LD, sitemaps, RSS (Campus Labs Engage), JSON / WordPress REST, server-rendered HTML (per-source selectors), headless browser as a last resort, the Hack Club API, manual entries and submissions. |
| `openroster/extract/` | Rule-based dates (never guessed; anything unclear goes to review), type/role/mode classification, and an offline gazetteer that places events relative to campuses. |
| `openroster/pipeline/` | Normalize, deduplicate across sources (keeping every source link), track moved and cancelled events, archive past ones. |
| `openroster/audit/` | `openroster audit <url>`: robots.txt, terms of use, platform detection, verdict. |
| `web/` | Next.js 16 site. Filters live in the URL, plus calendar view, digest, `.ics` and RSS feeds for every filtered view, no-JS fallback, and dark mode. |

## Commands

```bash
uv sync                                    # Python 3.12 + dependencies
uv run openroster audit https://example.edu/events   # verdict and reasons for any URL
uv run openroster audit --all              # audit every configured source → reports/source-audit.md
uv run openroster scrape                   # run every approved source, update data/
uv run openroster validate                 # schema + no-personal-data checks
uv run pytest                              # all adapters against saved fixtures (no network)

cd web && npm ci
npm run dev                                # site on http://localhost:3000 (reads ../data)
npm test && npm run e2e                    # unit tests; browser, no-JS and accessibility tests
```

## Rules

These are enforced in code and CI. See [CLAUDE.md](CLAUDE.md) for the full list.

- Public pages only, and only after an audit and the owner's sign-off (`reviewed: true`).
- Devpost and Eventbrite are blocked. MLH needs written permission. LinkedIn, Handshake and login portals are blocked. From Luma only official iCal links are used. Form hosts are linked, never fetched.
- Store facts and a ≤200-character summary in our own words, and link to the original. No copied descriptions, images or logos, and no personal data.
- Removal within 48 hours: [TAKEDOWN.md](TAKEDOWN.md).

## Docs

- [PLAN.md](PLAN.md): architecture and milestones
- [docs/decisions.md](docs/decisions.md): choices and reasons
- [docs/setup.md](docs/setup.md): one-time setup (GitHub, Vercel, secrets) and how to re-enable scheduled workflows
- [CONTRIBUTING.md](CONTRIBUTING.md): add a source, fix selectors, run tests
- [reports/source-audit.md](reports/source-audit.md): audit of every configured source

Data: place names from [GeoNames](https://www.geonames.org/) (CC BY 4.0). Some hackathon listings come from [Hack Club](https://hackathons.hackclub.com). Code: MIT.
