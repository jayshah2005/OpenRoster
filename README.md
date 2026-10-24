# OpenRoster

OpenRoster lists the events and programs that early-career computer science students usually hear about too late:
- bank and tech company info sessions
- student hackathons and their volunteer, mentor and judge calls
- career fairs and case competitions
- insight days and fellowships

It covers Ontario first, then the rest of Canada and the US. Everything is free, sorted by the nearest deadline, and linked to the organizer's own page.

**Site:** https://openroster-seven.vercel.app · **Browse on GitHub:** [LISTINGS.md](LISTINGS.md) · **Add something:** [submission form](../../issues/new?template=submit-opportunity.yml)

## What you can do with it

- **Filter the list:** events and recurring programs share one list, with filters in the left column: your year of study, what you want to do (attend, volunteer, mentor, judge), type, format, school or distance from a campus, dates, cost and who an event is for (first-year students, beginners, women and non-binary students and more). Your browser remembers your filters for next time, and they also live in the address, so any view can be bookmarked or shared.
- **Subscribe:** every view has a calendar feed. Events appear in Google Calendar, Apple Calendar or Outlook on their own, with an "Apply by" reminder the day before each deadline. RSS and a weekly digest are there too.
- **Read the guides:** the [Start here guide](https://openroster-seven.vercel.app/start/) explains each kind of opportunity and how to prepare. Insight days, first- and second-year programs, fellowships and scholarships that come back every year are in the main list too, and [/programs/](https://openroster-seven.vercel.app/programs/) shows only those.
- **Use the data:** calendar feeds, RSS and JSON are documented on the [data page](https://openroster-seven.vercel.app/data/).

## How it works

A Python pipeline reads public sources every 6 hours:
- school, club and Luma calendar feeds
- campus event APIs
- company student-event pages
- hackathon websites
- the Hack Club API
- submissions from students and organizers

It extracts dates and details with fixed rules, merges duplicates, and writes one JSON file per opportunity into `data/`. A Next.js site builds from those files and deploys to Vercel. GitHub Actions run all of it on the free tier. [docs/architecture.md](docs/architecture.md) has the details.

Collection follows strict rules, enforced in code:
- A person approves every source after an audit of its robots.txt and terms.
- The bot identifies itself and waits at least two seconds between requests to a site.
- Devpost, Eventbrite, LinkedIn, Handshake and login portals are never scraped. MLH needs written permission. Luma is read only through official calendar feeds.
- We store facts and a short summary in our own words, never descriptions, images or personal data.
- Unclear dates go to a person instead of being guessed.

Organizers can have a listing removed within 48 hours; see [TAKEDOWN.md](TAKEDOWN.md).

New sources are found every week: a rule-based pass checks the pages we already read for calendar feeds, and an optional agent searches the web. Both propose changes in a pull request that a person merges.

## Run it locally

```bash
uv sync && uv run pytest -q                                  # pipeline and its tests (no network)
uv run openroster audit https://example.edu/events           # robots.txt, terms and a verdict for any URL
OPENROSTER_DATA=/tmp/preview uv run python scripts/preview_from_fixtures.py
cd web && npm ci && OPENROSTER_DATA=/tmp/preview npm run dev # the site with sample data
```

## Contributing

You can add events, share calendars and fix listings without writing code, from the site or from GitHub. [CONTRIBUTING.md](CONTRIBUTING.md) covers that and code contributions.

| Document | What it covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | How the code fits together |
| [docs/setup.md](docs/setup.md) | One-time setup for maintainers |
| [docs/decisions.md](docs/decisions.md) | Why things are built the way they are |
| [reports/source-audit.md](reports/source-audit.md) | The audit of every configured source |

Place names come from [GeoNames](https://www.geonames.org/) (CC BY 4.0). Some hackathon listings come from [Hack Club](https://hackathons.hackclub.com).
