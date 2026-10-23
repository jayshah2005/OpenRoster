# Contributing

## Add an opportunity

Use the [submission form](../../issues/new?template=submit-opportunity.yml). The bot validates it and opens a PR. You don't need to touch code.

## Add a source (calendar feed, events page, hackathon site)

1. Add an entry to a file in `config/sources/` (or `config/hackathons.yaml`) with `reviewed: false`.
2. Run `uv run openroster audit <url>` and read the verdict. If robots.txt disallows it, its terms forbid automated access, or it needs a login, **stop**: ask the owner for a feed instead.
3. Pick the adapter. In order of preference:
   - `ics` (public iCal)
   - `tribe` or `localist` (campus calendar APIs)
   - `jsonld`
   - `rss` / `json`
   - `sitemap`
   - `html` with selectors
   - `headless` as a last resort
4. HTML sources: run `uv run openroster suggest-selectors <id> --html page.html` for starting selectors. After the source is approved, save a fixture with `uv run python scripts/capture_fixture.py <id>`.
5. Add or extend a fixture test. **Tests never use the network.**
6. Open a PR. Merging the daily **Source review** PR is the owner's sign-off that sets `reviewed: true`.

Never get around a login, CAPTCHA, bot check or rate limit, and never disguise the bot. Hosts in `config/known_verdicts.yaml` are refused in code.

## Develop

```bash
uv sync && uv run pytest && uv run ruff check openroster tests scripts && uv run mypy openroster
cd web && npm ci && npm run lint && npm run typecheck && npm test
# Site with fixture data (no network):
OPENROSTER_DATA=/tmp/preview uv run python scripts/preview_from_fixtures.py
cd web && OPENROSTER_DATA=/tmp/preview npm run build && npx next start -p 3123 &
npm run e2e && npm run check-size && npm run check-links
```

## Data rules

- **Dates:** never guessed. If a rule can't read a date with confidence, the item goes to the daily review PR with its evidence.
- **Summaries:** at most 200 characters, in our own words. Never copy a description.
- **Personal data:** none. No names, emails, phone numbers or photos of attendees, speakers, organizers or volunteers. `openroster validate` fails if a record contains an email address or phone number.
