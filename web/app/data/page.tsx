import type { Metadata } from "next";
import Link from "next/link";
import { REPO_URL, SITE_URL } from "@/lib/labels";

export const metadata: Metadata = {
  title: "Data and feeds",
  description: "Calendar feeds, RSS and JSON data for OpenRoster listings.",
};

// Public data docs. Lives at /data/ alongside the JSON files in public/data/ (meta.json, index*.json).
export default function DataPage() {
  return (
    <article className="prose">
      <h1>Data and feeds</h1>
      <p className="lede">
        Everything on OpenRoster is available as calendar feeds, RSS and plain JSON, free to use in your own projects.
        Please link back to the original listings.
      </p>

      <h2>Calendar and RSS for any view</h2>
      <p>
        Add the same filters you use on the site to these addresses. The calendar feed includes an &quot;Apply by&quot;
        reminder for every upcoming deadline; add <code>deadlines=0</code> to leave those out.
      </p>
      <pre>
        <code>{`${SITE_URL}/api/feed.ics?type=hackathon&role=volunteer\n${SITE_URL}/api/feed.rss?school=brock&km=50`}</code>
      </pre>
      <p>Filters you can combine:</p>
      <ul>
        <li><code>type</code>: hackathon, info_session, tech_talk, career_fair, networking, workshop, conference, case_competition, early_career_program</li>
        <li><code>role</code>: participant, volunteer, mentor, judge, organizer_team, workshop_lead</li>
        <li><code>school</code> with optional <code>km</code> (25, 50 or 100) for events near a campus</li>
        <li><code>region</code> (for example CA-ON), <code>country</code>, <code>mode</code> (in_person, online, hybrid)</li>
        <li><code>for</code>: first_year, second_year, beginner_friendly, women_nonbinary, black_students, indigenous_students, lgbtq, high_school</li>
        <li><code>open=1</code> for things open for applications now, <code>deadline=14</code> for deadlines within 14 days</li>
        <li><code>from</code> and <code>to</code> as dates (YYYY-MM-DD), <code>cost=free</code>, and <code>q</code> for text search</li>
      </ul>
      <p>
        Ready-made feeds that never change address: <a href="/feeds/all.ics">all.ics</a>,{" "}
        <a href="/feeds/all.rss">all.rss</a>, <a href="/feeds/new-today.rss">new-today.rss</a> and one per type, role,
        region and school (for example <a href="/feeds/type-hackathon.ics">type-hackathon.ics</a>).
      </p>

      <h2>JSON</h2>
      <p>
        <a href="/data/meta.json">/data/meta.json</a> lists the index files, and each index file is an array of upcoming
        listings with dates in ISO 8601, roles with their deadlines, location and tags. The full records, including
        sources and change history, are in the <a href={`${REPO_URL}/tree/main/data/records`}>repository</a>, one file
        per listing, and follow <a href={`${REPO_URL}/blob/main/schema/opportunity.schema.json`}>this JSON Schema</a>.
      </p>

      <h2>On GitHub</h2>
      <p>
        <a href={`${REPO_URL}/blob/main/LISTINGS.md`}>LISTINGS.md</a> is the same list as a table you can read on GitHub.
        Data refreshes every 6 hours. See <Link href="/about/">how the data is collected</Link>.
      </p>
    </article>
  );
}
