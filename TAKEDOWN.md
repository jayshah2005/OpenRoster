# Takedown policy

If you organize an event listed on OpenRoster, or run a site we collect from, you can ask us to remove a listing or to stop collecting from your site. **We act within 48 hours.**

## How to ask

- **GitHub:** [open a takedown request](../../issues/new?template=takedown.yml). It is public, so don't include private details.
- **Email:** `OPENROSTER_CONTACT` (the maintainer will put the real address here once the alias exists). Include the listing link (`…/o/<id>/`) or your site's domain.

## What happens

1. A bot immediately opens a pull request that adds the listing ID or your domain to `data/takedowns.json`.
2. A maintainer merges it. Reminders go out at 24 and 40 hours, so the 48-hour promise holds.
3. On the next update, about 6 hours later at most, the listing disappears from the site and feeds. Anything on the block list is never collected again.

A GitHub issue can't prove who sent it, so a person confirms each removal. We don't argue with removal requests from organizers: if you ask, it comes down.

## What we store

Facts (title, organizer, dates, place, eligibility, deadlines), a summary of at most 200 characters in our own words, and links to the original pages. We copy no descriptions, images or logos, and store no personal data. Our bot identifies itself as `OpenRosterBot` with a link to this repository, follows robots.txt, and waits at least 2 seconds between requests to a site.
