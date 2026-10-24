// /submit/: short entry point to the submission form; /contribute/ has the full picture.
import type { Metadata } from "next";
import Link from "next/link";
import { CONTACT_EMAIL, REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "Submit an opportunity" };

export default function SubmitPage() {
  return (
    <article className="prose">
      <h1>Submit an opportunity</h1>
      <p>
        Fill in the GitHub form with the title, official link, date and who can join. A bot checks it right away and a
        maintainer approves it, usually within a day.
      </p>
      <p className="actions">
        <a className="button" href={`${REPO_URL}/issues/new?template=submit-opportunity.yml`}>Open the form</a>
        <a className="button button-quiet" href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("New opportunity for OpenRoster")}`}>
          No GitHub account? Email it
        </a>
      </p>
      <p>
        We list hackathons, info sessions, tech talks, career fairs, networking events, workshops, conferences, case
        competitions and early-career programs, plus volunteer, mentor and judge calls. We do not list ordinary job or
        internship postings; <Link href="/also-useful/">these lists</Link> cover those.
      </p>
      <p>
        To share a whole club calendar, fix a listing or help with the code, see <Link href="/contribute/">Contribute</Link>.
      </p>
    </article>
  );
}
