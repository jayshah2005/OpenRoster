import type { Metadata } from "next";
import Link from "next/link";
import { CONTACT_EMAIL, REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <article className="prose">
      <h1>About OpenRoster</h1>
      <p className="lede">
        OpenRoster collects the events and programs that early-career computer science students usually hear about too
        late: bank and tech company info sessions, student hackathons and their volunteer calls, career fairs, case
        competitions, insight days and fellowships. It covers Ontario first, then the rest of Canada and the US.
      </p>
      <p>
        Event sites like Eventbrite and Luma carry some of this. Much of it lives elsewhere: on company careers pages,
        campus calendars, club calendars and hackathon websites. OpenRoster checks those places every 6 hours and puts
        what it finds in one list you can filter by school, distance, role and deadline.
      </p>

      <h2>Where listings come from</h2>
      <ul>
        <li>Public calendar feeds from schools, clubs and student communities.</li>
        <li>Campus event calendars and pages that publish structured event data.</li>
        <li>Student event pages from companies, read with a separate set of rules for each site.</li>
        <li>Hackathon websites, checked for dates and for volunteer, mentor and judge calls.</li>
        <li>
          Hack Club&apos;s public hackathon list, which is mostly high-school events (thanks to{" "}
          <a href="https://hackathons.hackclub.com">hackathons.hackclub.com</a>).
        </li>
        <li>Submissions from students, clubs, organizers and companies, and a weekly search for new sources.</li>
      </ul>

      <h2>How we collect it</h2>
      <p>
        Before any site is read, we check its robots.txt and its terms of use, and a maintainer approves it. Sites that
        forbid automated access, need a login or show a bot check are left alone; their events can still be submitted by
        hand. Our bot names itself, waits at least two seconds between requests to a site and reuses cached pages.
      </p>
      <p>
        We keep only the facts (title, organizer, dates, place, eligibility and deadlines) and a short summary in our own
        words, and we always link to the original page. We do not copy descriptions, images or logos, and we do not store
        names or contact details of attendees, speakers or organizers. Dates are read with fixed rules. When a date is
        unclear, a person checks it before the listing appears.
      </p>

      <h2>Privacy</h2>
      <p>
        There are no accounts, analytics or tracking cookies. Your filters live in the page address and your dark mode
        choice stays in your browser.
      </p>

      <h2>Who runs it</h2>
      <p>
        OpenRoster was started by a computer science student at Brock University and is open source. Questions and
        removal requests go to <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>. To help, see{" "}
        <Link href="/contribute/">Contribute</Link> or the code at <a href={REPO_URL}>{REPO_URL.replace("https://", "")}</a>.
      </p>

      <h2>Credits</h2>
      <p>
        Place names and coordinates come from <a href="https://www.geonames.org/">GeoNames</a> (CC BY 4.0). Code is MIT
        licensed.
      </p>
    </article>
  );
}
