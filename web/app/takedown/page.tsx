import type { Metadata } from "next";
import { REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "Takedown requests" };

const CONTACT = process.env.NEXT_PUBLIC_CONTACT_EMAIL;

export default function TakedownPage() {
  return (
    <article className="prose">
      <h1>Takedown requests</h1>
      <p>
        If you organize an event or run a site listed here and want a listing, or your whole site, removed, we remove
        it <strong>within 48 hours</strong>.
      </p>
      <p className="actions">
        <a className="button" href={`${REPO_URL}/issues/new?template=takedown.yml`}>Request removal on GitHub</a>
      </p>
      <p>
        {CONTACT ? (
          <>Or email <a href={`mailto:${CONTACT}`}>{CONTACT}</a></>
        ) : (
          <>Or email the address in <a href={`${REPO_URL}/blob/main/TAKEDOWN.md`}>TAKEDOWN.md</a></>
        )}{" "}
        with the listing link or your site&apos;s address.
      </p>
      <p>
        Removed listings and sites go on a block list so they are not collected again. A request from an address on the
        organizer&apos;s own domain is applied right away.
      </p>
      <p>Full policy: <a href={`${REPO_URL}/blob/main/TAKEDOWN.md`}>TAKEDOWN.md</a>.</p>
    </article>
  );
}
