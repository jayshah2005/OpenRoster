import type { Metadata } from "next";
import Link from "next/link";
import { REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "Submit an opportunity" };

export default function SubmitPage() {
  return (
    <article className="prose">
      <h1>Submit an opportunity</h1>
      <p>
        Students, clubs, organizers and companies can add or correct a listing with a short GitHub form. A bot checks
        it and opens a pull request; a maintainer approves it, usually within a day.
      </p>
      <p className="actions">
        <a className="button" href={`${REPO_URL}/issues/new?template=submit-opportunity.yml`}>Submit a new opportunity</a>
        <a className="button button-quiet" href={`${REPO_URL}/issues/new?template=correct-opportunity.yml`}>Correct a listing</a>
        <a className="button button-quiet" href={`${REPO_URL}/issues/new?template=add-source.yml`}>Suggest a calendar feed</a>
      </p>
      <h2>What we list</h2>
      <ul>
        <li>
          Hackathons (including company-run student hackathons), info sessions, tech talks, career fairs, networking
          events, workshops, conferences, case competitions and early-career programs such as fellowships,
          externships and first- and second-year programs.
        </li>
        <li>Calls for volunteers, mentors, judges, organizers and workshop leads, each with its own deadline.</li>
        <li>
          Not ordinary job or internship postings: see <Link href="/also-useful/">Also useful</Link> for those.
        </li>
      </ul>
      <h2>Tips</h2>
      <ul>
        <li>Use the official page link. Dates need a day, month and year.</li>
        <li>Hackathons hosted on Devpost or MLH can be submitted with your own official page or registration link.</li>
        <li>Please don&apos;t include personal names, emails or photos.</li>
        <li>
          Run a club calendar? Share its public iCal link (Google Calendar: Settings → &quot;Public address in iCal
          format&quot;) and every event will be added automatically.
        </li>
      </ul>
      <p>
        You need a free GitHub account to submit. Without one, use the contact address on the{" "}
        <Link href="/takedown/">takedown page</Link>.
      </p>
    </article>
  );
}
