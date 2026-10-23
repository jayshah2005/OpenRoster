# Research brief for source-mapping agents

OpenRoster collects opportunities for computer science students in Ontario, Canada (with national/online events too):
hackathons, info sessions, tech talks, career fairs, networking events, workshops, conferences, case competitions, and
early-career programs (fellowships, externships, first- and second-year programs). This includes volunteer, mentor,
judge, organizer and workshop-lead calls. Ordinary job and internship postings are OUT of scope.

Your job is to find **machine-readable or scrapable public sources** of those opportunities and record them as YAML.
The scraper itself is built later. You are only mapping and verifying sources.

## Hard rules (do not break any)
- Never fetch, and never list as a source, anything on: devpost.com (any subdomain), mlh.io / mlh.com, eventbrite.*,
  linkedin.com, joinhandshake.com, login-walled career portals (record only that they exist and need a login),
  Google Forms / Tally / Typeform / Jotform / Microsoft Forms (you may record such a link as a role's application link
  if it appears on an allowed page, but never open it).
- Luma (lu.ma / luma.com): never use its JSON/API endpoints. Record a Luma calendar only if it offers an official
  iCal subscription URL (the "Subscribe" → iCal link, typically `https://api.lu.ma/ics/get?entity=calendar&id=cal-…`),
  and record that URL.
- Never log in, never get around a CAPTCHA or bot check. If a page blocks you, record `blocked_by: bot_check`.
- No personal data: do not record names, emails or photos of people. A generic club or office contact address
  (like careers@school.ca) is fine to put in an `outreach_contact` field.
- Use WebSearch and WebFetch only; keep fetches modest (no crawling hundreds of pages).

## What to look for, and how to detect the platform
- WordPress "The Events Calendar": `<site>/wp-json/tribe/events/v1/events` returns JSON → `platform: tribe`.
- Localist: `<site>/api/2/events` returns JSON, or the page footer says Localist → `platform: localist`.
- ICS: "Subscribe", "iCal", "Export", ".ics", "webcal://" links. For Google Calendar embeds
  (`calendar.google.com/calendar/embed?src=<ID>`), the public feed is
  `https://calendar.google.com/calendar/ical/<ID URL-encoded>/public/basic.ics`. Verify it returns BEGIN:VCALENDAR.
- schema.org Event JSON-LD in `<script type="application/ld+json">` → `platform: jsonld`.
- A server-rendered HTML event list (events visible in the raw HTML) → `platform: html`.
- JS-only (the raw HTML has no events) → `platform: js_only`.
- Other campus platforms (CampusGroups, Ready Education, CampusLabs Engage/Presence, Orgsync, Brightspace,
  Experience portals): record the name, whether public pages work without login, and any public feed/API.
- robots.txt: fetch `<origin>/robots.txt` and note whether the event path is disallowed for `*`.
- Terms of use: find the terms/legal page URL from the footer and note any clause on scraping, crawling, automated
  access or republishing (quote at most 1–2 short sentences).

## Output format (YAML, exactly this shape)
```yaml
generated: 2026-10-23
agent: <your group name>
schools:            # only for school-research agents
  - id: brock                    # short slug
    name: Brock University
    kind: university | college
    website: https://brocku.ca
    campuses:
      - name: Main campus
        city: St. Catharines
        region: CA-ON
        lat: 43.1176
        lon: -79.2477
    hackathons:                  # run by or at this school
      - name: ...
        url: https://...         # official site, NOT devpost/mlh
        usual_month: January
        notes: ...
sources:
  - id: brock-events-calendar    # unique slug
    name: Brock University events calendar
    owner: brock | <org slug>
    url: https://...             # the exact feed/API/page URL the scraper should use
    landing_url: https://...     # the human page, if different
    platform: tribe | localist | ics | jsonld | html | js_only | api | sitemap | other
    expected_types: [info_session, workshop, ...]
    cs_relevance: high | medium | low   # how much CS-student content it carries
    login_required: false
    verified: true               # you actually fetched it and saw events / VCALENDAR / JSON
    sample_event_titles: ["..."] # 1-3 real titles you saw, to prove it works
    robots: allowed | disallowed | no_robots | unknown
    terms_url: https://...
    terms_notes: "..."           # quote or 'no clause found'
    blocked_by: null | bot_check | login | terms
    outreach_contact: null | generic office/club email
    notes: "..."
not_usable:         # things that exist but cannot be used, with the reason
  - name: ...
    url: ...
    reason: login_required | blocked_domain | js_only_no_feed | terms_forbid | dead
```
Write your file to the path given in your task. Prefer quality over quantity, but be thorough: for each school,
check the main events calendar, the career centre or co-op office events, the student union and clubs
directory (look specifically for CS, computing, engineering, women-in-tech, GDSC/Google Developer Student
Club, ACM, IEEE, data science, AI, cybersecurity, entrepreneurship and business-tech clubs), the CS department events
or seminar pages, and the school's hackathon(s).
