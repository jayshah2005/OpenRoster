# Contributing

Thanks for helping. Most contributions need no code at all.

## Without writing code

- **Add an event or program.** Use the [submission form](../../issues/new?template=submit-opportunity.yml). A bot checks it, opens a pull request, and a maintainer merges it. No GitHub account? Email the details to openroster@jayshah.xyz, or use the email button on the site's [Contribute page](https://openroster.vercel.app/contribute/).
- **Share a calendar.** If your club or school has a public Google Calendar, Luma calendar or events page, [suggest it](../../issues/new?template=add-source.yml). One calendar can bring in every future event automatically.
- **Fix a listing.** Every listing on the site has a "Report a problem" link that opens a [correction form](../../issues/new?template=correct-opportunity.yml) with the listing filled in.
- **Review.** Each week the discovery PR and each day the review PR list things a person should check. Comments on those PRs help.

## With code

Start with [docs/architecture.md](docs/architecture.md), which follows one listing from a website to the page and lists where common changes go.

### Set up

```bash
uv sync                                     # Python 3.12 and dependencies
uv run pytest -q                            # every adapter against saved fixtures, no network
cd web && npm ci && npm run dev             # the site on http://localhost:3000, reading ../data
```

To see the site with sample data instead of an empty list:

```bash
OPENROSTER_DATA=/tmp/preview uv run python scripts/preview_from_fixtures.py
cd web && OPENROSTER_DATA=/tmp/preview npm run dev
```

### Before you open a pull request

```bash
uv run ruff check openroster tests scripts && uv run mypy openroster && uv run pytest -q && uv run openroster validate
cd web && npm run lint && npm run typecheck && npm test
```

CI also builds the site, runs browser and accessibility tests, checks the 300 kB first-load budget and crawls every internal link.

### Commit messages

`type/scope: summary`, for example `feat/adapters/rss: add engage rss adapter` or `fix/extract: read "pm AT" as atlantic time`. The types are feat, fix, refactor and chore. The scopes are listed in [.claude/skills/commit-convention/SKILL.md](.claude/skills/commit-convention/SKILL.md). Keep each commit to one change.

### Adding a source

1. Add an entry to a file in `config/sources/` with `reviewed: false`.
2. Run `uv run openroster audit <url>`. If robots.txt disallows the page, the terms forbid automated access, or it needs a login, stop and ask the site for a feed instead.
3. Prefer a feed over a page. In order: `ics`, `tribe` or `localist`, `jsonld`, `rss` or `json`, `sitemap`, then `html` with selectors, and `headless` only when nothing else works.
4. For HTML sources, `uv run openroster suggest-selectors <id> --html page.html` proposes selectors. Once the owner has approved the source, `uv run python scripts/capture_fixture.py <id>` saves a sanitized copy of the page as a test fixture.
5. Open a pull request. The source starts collecting after the owner merges the Source review PR.

Never get around a login, a CAPTCHA, a bot check or a rate limit, and never disguise the bot. The hosts in `config/known_verdicts.yaml` are refused in code.

### Data rules

- Dates are never guessed. Anything unclear goes to the review PR with its evidence.
- Summaries are at most 200 characters and in our own words. Do not copy descriptions.
- No personal data: no names, emails, phone numbers or photos of attendees, speakers, organizers or volunteers. `openroster validate` fails if a record contains an email address or phone number.
