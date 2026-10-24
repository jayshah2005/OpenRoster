// One opportunity in a list: date tile, type, title, when/where/who, ways to take part and the next deadline.
// Server and client safe (used by the static list and by the filtered results).
import Link from "next/link";
import { fmtDate, fmtWhen } from "@/lib/format";
import { AUDIENCE_LABEL, MODE_LABEL, ROLE_LABEL, TYPE_LABEL, regionName } from "@/lib/labels";
import { YEAR_LABEL } from "@/lib/directory";
import type { Entry, Program } from "@/lib/types";
import { Icon } from "./Icon";

export function nextDeadline(e: Entry, nowIso: string): string | null {
  const now = Date.parse(nowIso);
  const open = e.roles.map((r) => r.closes).filter((d): d is string => !!d && Date.parse(d) >= now);
  return open.sort((a, b) => Date.parse(a) - Date.parse(b))[0] ?? null; // parse: offsets differ (-04:00, Z)
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

const SKIP = new Set(["the", "of", "and", "for", "a", "an", "&"]);

/**
 * A coloured tile with the organization's initials. We never copy logos or images (facts only, see TAKEDOWN.md),
 * so this is drawn here: the colour comes from a hash of the name, so each organization keeps the same one.
 */
export function Monogram({ name }: { name: string }) {
  const words = name.replace(/\(.*?\)/g, "").split(/[\s/-]+/).filter((w) => w && !SKIP.has(w.toLowerCase()));
  const initials = (words.length > 1 ? words[0][0] + words[1][0] : (words[0] ?? "?").slice(0, 2)).toUpperCase();
  let hue = 0;
  for (const ch of name) hue = (hue * 31 + ch.charCodeAt(0)) % 360;
  return (
    <div className="monogram" style={{ "--hue": hue } as React.CSSProperties} aria-hidden="true">
      {initials}
    </div>
  );
}

const KIND_LABEL: Record<string, string> = { program: "Program", insight: "Insight program", fellowship: "Fellowship" };

/** A recurring program (config/programs.yaml): no fixed date, so it links straight to the official page. */
export function ProgramCard({ p }: { p: Program }) {
  const years = p.years.length ? p.years.map((y) => YEAR_LABEL[y] ?? `Year ${y}`).join(", ") : "Any year";
  return (
    <li className="card card-program">
      <Monogram name={p.organization ?? p.name} />
      <div className="card-body">
        <div className="card-top">
          <span className="tag tag-program">{KIND_LABEL[p.kind] ?? "Program"}</span>
          <span className="badge">Recurring</span>
        </div>
        <h3 className="card-title">
          <a href={p.url} rel="noopener">{p.name}</a>
        </h3>
        <ul className="card-meta">
          {p.organization && <li><Icon name="org" size={14} /> {p.organization}</li>}
          <li><Icon name="user" size={14} /> {years}</li>
          {p.timing && <li><Icon name="clock" size={14} /> {p.timing}</li>}
        </ul>
        <p className="card-summary">{p.who}</p>
      </div>
    </li>
  );
}
