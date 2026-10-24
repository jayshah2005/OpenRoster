# How OpenRoster works

This guide is for people reading the code for the first time. It follows one listing from a source website to the page a student sees, then explains where to make common changes.

## The two halves

OpenRoster is a Python data pipeline (`openroster/`) and a Next.js website (`web/`). They meet in one place: the pipeline writes JSON files into `data/`, and the website reads those files when it builds. Neither half calls the other, so you can work on either without running the other.

GitHub Actions run the pipeline every 6 hours. When the data changes, the workflow commits it, and the site rebuilds and deploys.

```
config/  ─►  openroster scrape  ─►  data/records/*.json  ─►  web (next build)  ─►  Vercel
 (what to       (fetch, extract,       (one file per            (static pages,
  collect)       merge, archive)        opportunity)             feeds, JSON)
```

## From a source to a listing

1. **Configuration.** Each source is an entry in `config/sources/*.yaml`. It names an adapter (`ics`, `tribe`, `localist`, `jsonld`, `sitemap`, `rss`, `json`, `html`, `headless` or `hackclub`), a URL, and options such as CSS selectors or a keyword filter. A source runs only when its latest audit says `allowed` and the owner has set `reviewed: true`. `Source.runnable` in `openroster/config.py` is the one place that decides this.

2. **Fetching.** Adapters never use HTTP directly. They call `Fetcher.get()` in `openroster/fetch.py`, which:
   - refuses hosts on the blocked list (`config/known_verdicts.yaml`)
   - checks robots.txt on every URL and redirect
   - waits at least 2 seconds per host, or longer if the site's Crawl-delay asks
   - sends conditional requests from a cache, backs off on errors, and stops at the source's page budget

   If you change how the bot talks to websites, change it here and nowhere else.

3. **Adapters** (`openroster/adapters/`) turn a response into `Candidate` objects (`adapters/base.py`). A candidate is raw: a title, a URL, dates if the source gave them, and some text used only for keyword rules. Adapters do not decide types or roles. When a source gives no reliable date, the candidate carries `review_reasons` instead of a guess.

4. **Extraction** (`openroster/extract/`):
   - `dates.py` reads dates out of prose with fixed rules and returns a confidence. It never guesses a year unless the source config allows it.
   - `classify.py` assigns the type, roles, mode, eligibility, cost and audience tags with keyword rules.
   - `geo.py` places events using a bundled city list and works out which campuses they are near.

5. **Normalizing** (`pipeline/normalize.py`) turns a candidate into an `Opportunity` (`openroster/model.py`, the schema), or into a review item when the date is not certain. It also writes the short summary in our own words and strips speaker names from titles.

6. **Merging** (`pipeline/merge.py`) matches the new record to existing ones. It matches on:
   - the same source ID first
   - then the same URL
   - then a similar title on the same day in the same city

   Duplicates from different sources become one record that keeps every source link. Moved and cancelled events are tracked in `history`.

7. **Running** (`pipeline/run.py`) ties steps 2 to 6 together for every source. It then:
   - archives past events
   - writes only the files that changed
   - records each source's health
   - writes the review queue for anything held back

8. **The website** (`web/`):
   - `web/scripts/gen-data.mjs` turns `data/` and `config/` into JSON modules and the public `data/*.json` index.
   - Every page under `web/app/` is prerendered (the root layout sets `ensureStatic = "navigation"`).
   - Filtering happens in the browser with `web/lib/filter.ts`. The same file powers `/api/feed.ics` and `/api/feed.rss`, so a subscribed feed always matches the page.

## The jobs around it

| Workflow | What it does |
|---|---|
| `scrape.yml` | Every 6 hours: scrape, validate, update `LISTINGS.md`, commit, deploy, and open or close health issues |
| `audit.yml` | Daily and on config changes: audit every source and open the Source review PR that the owner merges to approve sources |
| `discover.yml` | Weekly: rule-based discovery plus an optional search agent; proposes new sources and events in a PR |
| `review.yml` | Daily PR with held-back items as fill-in YAML stubs |
| `selectors.yml` | Weekly: rule-based selectors for approved HTML sources that have none, proposed in a PR |
| `submission.yml` | Turns issue forms (submit, correct, takedown, permission) into PRs |
| `ci.yml` | Lint, types, tests with saved fixtures, site build, size budget, link check, accessibility |
| `ai.yml` | Optional helpers: selector repair, review suggestions, terms summaries, `@claude` |

The Python side of each job lives in `openroster/ops/`. The CLI (`openroster/cli.py`) is the entry point for all of them, so every workflow step can be run on your machine.

## Where to make common changes

| You want to | Change |
|---|---|
| Add a source that uses a supported platform | An entry in `config/sources/*.yaml`, then `uv run openroster audit <url>` |
| Support a new kind of source | A new `Adapter` subclass in `openroster/adapters/`, registered in `adapters/__init__.py`, plus a fixture test in `tests/test_adapters.py` |
| Fix selectors for an HTML source | Its `options` in `config/sources/`; `openroster suggest-selectors <id>` proposes some; keep `tests/fixtures/sources/<id>.html` parsing |
| Recognize a new date format | `openroster/extract/dates.py` and `tests/test_dates.py` |
| Improve type, role or audience rules | `openroster/extract/classify.py` |
| Add a field to listings | `openroster/model.py`, then `uv run openroster schema`, then `web/lib/types.ts` and `web/scripts/gen-data.mjs` |
| Add a filter to the site | `web/lib/filter.ts` (logic and URL key), `web/components/FilterForm.tsx` (control), `web/tests/filter.test.ts` |
| Change site copy | `web/app/**/page.tsx`. Keep it plain; see `.claude/skills/humanizer/SKILL.md` |

## Rules that the code enforces

The hard rules in `CLAUDE.md` are checked, not just documented:
- blocked hosts are refused in `fetch.py`
- sources need the sign-off flag in `config.py`
- personal data fails `openroster validate`
- uncertain dates go to review in `normalize.py`
- every adapter has a fixture test that never touches the network
