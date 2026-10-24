// /o/<id>/: one opportunity with every role, its window, sources and "last verified" date.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { LocalTime } from "@/components/LocalTime";
import { allIds, getOpportunity, schoolById } from "@/lib/data";
import { fmtDate, fmtDateTime, fmtWhen } from "@/lib/format";
import {
  ELIG_LABEL, REGION_LABEL, REPO_URL, ROLE_LABEL, ROUTE_LABEL, SITE_URL, TYPE_LABEL, TYPE_PLURAL,
} from "@/lib/labels";

export function generateStaticParams() {
  const ids = allIds();
  return (ids.length ? ids : ["placeholder"]).map((id) => ({ id }));
}

export async function generateMetadata({ params }: PageProps<"/o/[id]">): Promise<Metadata> {
  const o = getOpportunity((await params).id);
  return o ? { title: o.title, description: o.summary } : { title: "Not found" };
}

export default async function OpportunityPage({ params }: PageProps<"/o/[id]">) {
  const o = getOpportunity((await params).id);
  if (!o) notFound();
  const where =
    o.mode === "online"
      ? "Online"
      : [o.location.venue_name, o.location.city, o.location.region ? REGION_LABEL[o.location.region] ?? o.location.region : null]
          .filter(Boolean)
          .join(", ") || "Not stated";
  const schoolNames = o.schools.includes("open_to_all")
    ? null
    : o.schools.map((s) => schoolById.get(s)?.name ?? s).join(", ");
  const report = new URLSearchParams({
    template: "correct-opportunity.yml",
    title: `Correction: ${o.title}`,
    opportunity_id: o.id,
    page_url: `${SITE_URL}/o/${o.id}/`,
  });
  const original = o.registration.url ?? o.sources[0].url;

  return (
    <article className="opp">
      <p className="crumbs">
        <Link href="/">All opportunities</Link> / <Link href={`/type/${o.type}/`}>{TYPE_PLURAL[o.type]}</Link>
      </p>
      {o.status === "past" && <p className="notice">This event has passed.</p>}
      {o.status === "cancelled" && <p className="notice notice-warn">The source marked this event as cancelled.</p>}
      {o.status === "moved" && <p className="notice notice-warn">The date of this event changed. Check the original page.</p>}
      <p className="card-top"><span className={`tag tag-${o.type}`}>{TYPE_LABEL[o.type]}</span></p>
      <h1>{o.title}</h1>
      <p className="lede">{o.summary}</p>
      <dl className="facts">
        <dt>When</dt>
        <dd>
          {fmtWhen(o)}
          <br />
          <LocalTime start={o.start} tz={o.timezone} />
        </dd>
        <dt>Where</dt>
        <dd>{where}{o.mode === "hybrid" && " (hybrid)"}</dd>
        <dt>Organizer</dt>
        <dd>{o.organizer}</dd>
        <dt>Who can join</dt>
        <dd>
          {o.eligibility.map((e) => ELIG_LABEL[e]).join(", ")}
          {schoolNames && ` · ${schoolNames}`}
        </dd>
        <dt>Cost</dt>
        <dd>
          {{ free: "Free", paid: "Paid", unknown: "Not stated" }[o.cost.kind]}
          {o.travel_support.stated && " · travel support mentioned"}
        </dd>
        <dt>How to register</dt>
        <dd>{ROUTE_LABEL[o.registration.route] ?? ROUTE_LABEL.unknown}</dd>
      </dl>

      <h2>Ways to take part</h2>
      <div className="table-wrap">
        <table className="roles-table">
          <thead>
            <tr><th scope="col">Role</th><th scope="col">Opens</th><th scope="col">Closes</th><th scope="col">Status</th></tr>
          </thead>
          <tbody>
            {o.roles.map((r) => (
              <tr key={r.role}>
                <th scope="row">{r.url ? <a href={r.url} rel="nofollow noopener">{ROLE_LABEL[r.role]}</a> : ROLE_LABEL[r.role]}</th>
                <td>{r.opens ? fmtDateTime(r.opens, o.timezone) : "—"}</td>
                <td>{r.closes ? fmtDateTime(r.closes, o.timezone) : "—"}</td>
                <td>{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="actions">
        <a className="button" href={original} rel="nofollow noopener">Go to the original page</a>
        <a className="button button-quiet" href={`/o/${o.id}/event.ics`}>Add to calendar</a>
      </p>

      <h2>Sources</h2>
      <ul className="sources">
        {o.sources.map((s) => (
          <li key={`${s.source_id}|${s.url}`}><a href={s.url} rel="nofollow noopener">{s.url}</a></li>
        ))}
      </ul>
      <p className="verified">
        Last verified on {fmtDate(o.last_verified)} · first seen {fmtDate(o.first_seen)}
      </p>
      {o.history.length > 0 && (
        <details>
          <summary>Change history</summary>
          <ul>
            {o.history.map((h) => (
              <li key={`${h.at}${h.field}`}>{fmtDate(h.at)}: {h.field} changed from {h.old ?? "—"} to {h.new ?? "—"}</li>
            ))}
          </ul>
        </details>
      )}
      <p className="report">
        <a href={`${REPO_URL}/issues/new?${report.toString()}`}>Report a problem with this listing</a>
      </p>
    </article>
  );
}
