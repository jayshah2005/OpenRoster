import type { Metadata } from "next";
import { REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <article className="prose">
      <h1>About OpenRoster</h1>
      <p>
        OpenRoster collects opportunities for computer science students in one filterable place: hackathons, info
        sessions, tech talks, career fairs, networking events, workshops, conferences, case competitions and
        early-career programs, plus calls for volunteers, mentors, judges, organizers and workshop leads. It covers
        Ontario first, then the rest of Canada and the US.
      </p>
      <h2>Where the data comes from</h2>
      <ul>
        <li>Public calendar feeds (iCal) from schools, clubs and communities, including official Luma iCal links.</li>
        <li>Public campus calendar APIs and pages that publish schema.org event data.</li>
        <li>Public event pages from companies and organizations, read with per-site rules.</li>
        <li>Hackathon websites, checked for dates and volunteer, mentor and judge calls.</li>
        <li>
          Hack Club&apos;s public hackathon list, which is mostly high-school events (credit:{" "}
          <a href="https://hackathons.hackclub.com">hackathons.hackclub.com</a>).
        </li>
        <li>Submissions from students, clubs, organizers and companies, and a hand-curated list of programs.</li>
      </ul>
      <h2>Rules we follow</h2>
      <ul>
        <li>
          A person approves every source after an audit of its robots.txt and terms of use. Sites that forbid
          automated access, need a login, or show a bot check are never scraped.
        </li>
        <li>The bot names itself, waits at least two seconds between requests to a site, and caches pages.</li>
        <li>
          We store facts only (title, organizer, dates, place, eligibility, deadlines) and a short summary in our own
          words, and always link to the original. We copy no descriptions, images or logos.
        </li>
        <li>We store no personal data about attendees, speakers, organizers or volunteers.</li>
        <li>Dates are read with fixed rules. An unclear date is never guessed; a person checks it first.</li>
      </ul>
      <h2>Privacy</h2>
      <p>
        No accounts, analytics or tracking cookies. Filters live only in the page address. Your dark-mode choice is
        stored in your browser.
      </p>
      <h2>Credits</h2>
      <p>
        Place names and coordinates: <a href="https://www.geonames.org/">GeoNames</a> (CC BY 4.0). OpenRoster is open
        source: <a href={REPO_URL}>{REPO_URL}</a>.
      </p>
    </article>
  );
}
