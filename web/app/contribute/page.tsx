// /contribute/: every way to help, from the website (email) or GitHub (issue forms, code).
import type { Metadata } from "next";
import Link from "next/link";
import { CONTACT_EMAIL, REPO_URL } from "@/lib/labels";

export const metadata: Metadata = {
  title: "Contribute",
  description: "Add an event, share a club calendar, fix a listing or help build OpenRoster.",
};

const issue = (template: string) => `${REPO_URL}/issues/new?template=${template}`;

// A prefilled email for people without a GitHub account. The fields mirror the submission form.
const mailBody = encodeURIComponent(
  [
    "Title:",
    "Type (hackathon, info session, tech talk, career fair, workshop, conference, case competition, program, other):",
    "Organizer:",
    "Official link:",
    "Date and time (and time zone):",
    "In person, online or hybrid? City:",
    "Ways to take part (attend, volunteer, mentor, judge) and deadlines:",
    "Who can join:",
  ].join("\n\n"),
);

export default function ContributePage() {
  return (
    <article className="prose">
      <h1>Contribute</h1>
      <p className="lede">
        OpenRoster is maintained by students and run in the open. Most events reach the site because someone added them
        or shared a calendar, so every submission helps.
      </p>

      <h2>Add an event or program</h2>
      <p>
        Use the GitHub form. It asks for the title, link, date and who can join, checks your answers right away, and a
        maintainer approves it, usually within a day. You need a free GitHub account.
      </p>
      <p className="actions">
        <a className="button" href={issue("submit-opportunity.yml")}>Submit on GitHub</a>
        <a className="button button-quiet" href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("New opportunity for OpenRoster")}&body=${mailBody}`}>
          Submit by email instead
        </a>
      </p>
      <p>
        Volunteer, mentor and judge calls count too: list each role with its own deadline. Please do not include
        anyone&apos;s name, email or photo.
      </p>

      <h2>Share a club or campus calendar</h2>
      <p>
        If your club keeps a public Google Calendar, every event on it can appear here automatically. In Google Calendar,
        open the calendar&apos;s settings and copy &quot;Public address in iCal format&quot;, then{" "}
        <a href={issue("add-source.yml")}>send us the link</a>. Events pages, Luma calendars and hackathon websites are
        welcome too. Before anything is collected, we check the site&apos;s robots.txt and terms, and a maintainer
        approves it.
      </p>

      <h2>Fix a listing</h2>
      <p>
        Every listing has a &quot;Report a problem&quot; link that opens a form with the listing already filled in. Wrong
        dates, a moved event and a broken link are all worth reporting.
      </p>

      <h2>Organizers</h2>
      <p>
        If you run an event, add it with the form above or share your calendar. If you would rather not be listed,{" "}
        <Link href="/takedown/">ask for removal</Link> and it comes down within 48 hours.
      </p>

      <h2>Help build it</h2>
      <p>
        The code is open source. The data pipeline is Python and the site is Next.js. Good first tasks include writing
        page selectors for a new source, improving how dates or event types are recognized, and design or accessibility
        fixes. Start with the{" "}
        <a href={`${REPO_URL}/blob/main/CONTRIBUTING.md`}>contributing guide</a> and the{" "}
        <a href={`${REPO_URL}/blob/main/docs/architecture.md`}>architecture overview</a>, or browse{" "}
        <a href={`${REPO_URL}/issues`}>open issues</a>.
      </p>

      <h2>Spread the word</h2>
      <p>
        Share the site with your club or class, or put a filtered link in your club newsletter, for example{" "}
        <Link href="/?type=hackathon&amp;open=1">hackathons open for applications</Link>. You can also use the{" "}
        <Link href="/data/">feeds and data files</Link> in your own projects.
      </p>
    </article>
  );
}
