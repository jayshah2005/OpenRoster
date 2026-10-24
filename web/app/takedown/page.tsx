// /takedown/: how organizers ask for removal (TAKEDOWN.md has the full policy).
import type { Metadata } from "next";
import { CONTACT_EMAIL, REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "Remove a listing" };

export default function TakedownPage() {
  return (
    <article className="prose">
      <h1>Remove a listing</h1>
      <p>
        If you organize an event listed here, or run a site we collect from, we will remove the listing or stop
        collecting from your site within 48 hours of your request.
      </p>
      <p className="actions">
        <a className="button" href={`${REPO_URL}/issues/new?template=takedown.yml`}>Request removal on GitHub</a>
        <a className="button button-quiet" href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("Removal request")}`}>
          Email {CONTACT_EMAIL}
        </a>
      </p>
      <p>
        Include the listing&apos;s address (it contains /o/) or your site&apos;s domain. GitHub issues are public, so use
        email if you would rather keep the request private.
      </p>
      <p>
        Removed listings and sites go on a block list and are not collected again. The full policy is in{" "}
        <a href={`${REPO_URL}/blob/main/TAKEDOWN.md`}>TAKEDOWN.md</a>.
      </p>
    </article>
  );
}
