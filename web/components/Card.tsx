// One opportunity in a list: date tile, type, title, when/where/who, ways to take part and the next deadline.
// Server and client safe (used by the static list and by the filtered results).
import Link from "next/link";
import { fmtDate, fmtWhen } from "@/lib/format";
import { AUDIENCE_LABEL, MODE_LABEL, ROLE_LABEL, TYPE_LABEL, regionName } from "@/lib/labels";
import type { Entry } from "@/lib/types";
import { Icon } from "./Icon";

export function nextDeadline(e: Entry, nowIso: string): string | null {
  return e.roles.map((r) => r.closes).filter((d): d is string => !!d && d >= nowIso).sort()[0] ?? null;
}

function tile(iso: string, tz: string): { month: string; day: string } {
  const d = new Date(iso);
  return {
    month: new Intl.DateTimeFormat("en-CA", { timeZone: tz, month: "short" }).format(d).replace(".", ""),
    day: new Intl.DateTimeFormat("en-CA", { timeZone: tz, day: "numeric" }).format(d),
  };
}

/** "soon" within 7 days, "urgent" within 3: colours the deadline so the closest ones stand out. */
function urgency(deadline: string, nowIso: string): { cls: string; left: string } {
  const days = Math.ceil((new Date(deadline).getTime() - new Date(nowIso).getTime()) / 86_400_000);
  const left = days <= 0 ? "closes today" : days === 1 ? "1 day left" : `${days} days left`;
  return { cls: days <= 3 ? "urgent" : days <= 7 ? "soon" : "", left };
}

export function Card({ e, nowIso }: { e: Entry; nowIso: string }) {
  const dl = nextDeadline(e, nowIso);
  const u = dl ? urgency(dl, nowIso) : null;
  const t = tile(e.start, e.timezone);
  const place =
    e.mode === "online"
      ? "Online"
      : [e.city, e.region ? regionName(e.region) : null].filter(Boolean).join(", ") || MODE_LABEL[e.mode];
  const audience = e.tags.filter((tag) => tag in AUDIENCE_LABEL);
  return (
    <li className={`card${e.status === "cancelled" ? " is-cancelled" : ""}`}>
      <div className="date-tile" aria-hidden="true">
        <span className="month">{t.month}</span>
        <span className="day">{t.day}</span>
      </div>
      <div className="card-body">
        <div className="card-top">
          <span className={`tag tag-${e.type}`}>{TYPE_LABEL[e.type]}</span>
          {e.status === "cancelled" && <span className="badge badge-warn">Cancelled</span>}
          {e.status === "moved" && <span className="badge badge-warn">Date changed</span>}
          {e.cost === "free" && <span className="badge">Free</span>}
          {e.tags.includes("mostly_high_school") && <span className="badge">Mostly high school</span>}
          {audience.map((tag) => <span key={tag} className="badge badge-accent">{AUDIENCE_LABEL[tag]}</span>)}
        </div>
        <h3 className="card-title">
          <Link href={`/o/${e.id}/`} prefetch={false}>{e.title}</Link>
        </h3>
        <ul className="card-meta">
          <li><Icon name="clock" size={14} /> {fmtWhen(e)}</li>
          <li><Icon name="pin" size={14} /> {place}</li>
          <li><Icon name="org" size={14} /> {e.organizer}</li>
        </ul>
        <div className="card-foot">
          <ul className="roles" aria-label="Ways to take part">
            {e.roles.map((r) => (
              <li key={r.role} className={`role role-${r.status}`}>{ROLE_LABEL[r.role]}</li>
            ))}
          </ul>
          {dl && u && (
            <p className={`deadline ${u.cls}`}>
              Apply by <time dateTime={dl}>{fmtDate(dl, e.timezone)}</time>
              <span className="left"> · {u.left}</span>
            </p>
          )}
        </div>
      </div>
    </li>
  );
}

export function CardList({ items, nowIso }: { items: Entry[]; nowIso: string }) {
  if (!items.length) {
    return (
      <div className="empty">
        <p className="empty-title">Nothing matches yet.</p>
        <p>
          Try removing a filter, or <Link href="/contribute/">add an event you know about</Link>.
        </p>
      </div>
    );
  }
  return (
    <ul className="cards">
      {items.map((e) => <Card key={e.id} e={e} nowIso={nowIso} />)}
    </ul>
  );
}
