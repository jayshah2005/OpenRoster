import Link from "next/link";
import { fmtDate, fmtWhen } from "@/lib/format";
import { MODE_LABEL, ROLE_LABEL, TYPE_LABEL, regionName } from "@/lib/labels";
import type { Entry } from "@/lib/types";

export function nextDeadline(e: Entry, nowIso: string): string | null {
  return e.roles.map((r) => r.closes).filter((d): d is string => !!d && d >= nowIso).sort()[0] ?? null;
}

export function Card({ e, nowIso }: { e: Entry; nowIso: string }) {
  const dl = nextDeadline(e, nowIso);
  const place = e.mode === "online" ? "Online" : [e.city, e.region ? regionName(e.region) : null].filter(Boolean).join(", ") || MODE_LABEL[e.mode];
  return (
    <li className={`card${e.status === "cancelled" ? " is-cancelled" : ""}`}>
      <div className="card-top">
        <span className={`tag tag-${e.type}`}>{TYPE_LABEL[e.type]}</span>
        {e.status === "cancelled" && <span className="badge badge-warn">Cancelled</span>}
        {e.status === "moved" && <span className="badge badge-warn">Date changed</span>}
        {e.tags.includes("mostly_high_school") && <span className="badge">Mostly high school</span>}
        {e.cost === "free" && <span className="badge">Free</span>}
      </div>
      <h3 className="card-title">
        <Link href={`/o/${e.id}/`} prefetch={false}>{e.title}</Link>
      </h3>
      <p className="card-meta">
        <span>{fmtWhen(e)}</span>
        <span>{place}</span>
        <span>{e.organizer}</span>
      </p>
      <ul className="roles" aria-label="Ways to take part">
        {e.roles.map((r) => (
          <li key={r.role} className={`role role-${r.status}`}>
            {ROLE_LABEL[r.role]}
            {r.closes && ` · apply by ${fmtDate(r.closes, e.timezone)}`}
            {r.status === "closed" && " (closed)"}
          </li>
        ))}
      </ul>
      {dl && (
        <p className="deadline">
          Next deadline: <time dateTime={dl}>{fmtDate(dl, e.timezone)}</time>
        </p>
      )}
    </li>
  );
}

export function CardList({ items, nowIso }: { items: Entry[]; nowIso: string }) {
  if (!items.length) return <p className="empty">Nothing matches. Try removing a filter, or <Link href="/submit/">submit an opportunity</Link>.</p>;
  return (
    <ul className="cards">
      {items.map((e) => <Card key={e.id} e={e} nowIso={nowIso} />)}
    </ul>
  );
}
