// iCalendar (RFC 5545) and RSS 2.0 writers. Times are written in UTC so no VTIMEZONE blocks are needed.
import { fmtWhen } from "./format";
import { ROLE_LABEL, SITE_URL, TYPE_LABEL } from "./labels";
import type { Entry } from "./types";

function icsEscape(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
}

/** Fold lines at 75 octets as RFC 5545 requires. */
function fold(line: string): string {
  const bytes = new TextEncoder().encode(line);
  if (bytes.length <= 75) return line;
  const out: string[] = [];
  let cur = "";
  let curLen = 0;
  for (const ch of line) {
    const len = new TextEncoder().encode(ch).length;
    if (curLen + len > (out.length ? 74 : 75)) {
      out.push(cur);
      cur = "";
      curLen = 0;
    }
    cur += ch;
    curLen += len;
  }
  out.push(cur);
  return out.join("\r\n ");
}

const utc = (iso: string) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");

function localDate(iso: string, tz: string, addDays = 0): string {
  const d = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" })
    .format(new Date(iso));
  const dt = new Date(`${d}T12:00:00Z`);
  dt.setUTCDate(dt.getUTCDate() + addDays);
  return dt.toISOString().slice(0, 10).replace(/-/g, "");
}

/**
 * Calendar feed. Each opportunity is one event; with `deadlines` (the default), every upcoming application
 * deadline is also its own short "Apply by" event, so a subscribed calendar reminds people before it closes.
 */
export function toICS(entries: Entry[], name: string, opts: { deadlines?: boolean; now?: string } = {}): string {
  const withDeadlines = opts.deadlines ?? true;
  const now = opts.now ?? new Date().toISOString();
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//OpenRoster//openroster//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    `X-WR-CALNAME:${icsEscape(`OpenRoster: ${name}`)}`,
    "X-PUBLISHED-TTL:PT6H",
    "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
  ];
  for (const e of entries) {
    const page = `${SITE_URL}/o/${e.id}/`;
    const desc = [
      e.summary,
      "",
      ...e.roles.filter((r) => r.closes).map((r) => `${ROLE_LABEL[r.role]}: apply by ${r.closes!.slice(0, 10)}`),
      "",
      `Details and source: ${page}`,
    ].join("\n");
    lines.push("BEGIN:VEVENT", `UID:${e.id}@openroster`, `DTSTAMP:${utc(e.last_verified)}`);
    if (e.all_day) {
      lines.push(`DTSTART;VALUE=DATE:${localDate(e.start, e.timezone)}`);
      lines.push(`DTEND;VALUE=DATE:${localDate(e.end ?? e.start, e.timezone, 1)}`);
    } else {
      lines.push(`DTSTART:${utc(e.start)}`);
      lines.push(`DTEND:${utc(e.end ?? new Date(new Date(e.start).getTime() + 3_600_000).toISOString())}`);
    }
    lines.push(`SUMMARY:${icsEscape((e.status === "cancelled" ? "CANCELLED: " : "") + e.title)}`);
    lines.push(`DESCRIPTION:${icsEscape(desc)}`, `URL:${page}`);
    const loc = e.mode === "online" ? "Online" : [e.city, e.region?.split("-")[1]].filter(Boolean).join(", ");
    if (loc) lines.push(`LOCATION:${icsEscape(loc)}`);
    lines.push(`CATEGORIES:${icsEscape(TYPE_LABEL[e.type] ?? e.type)}`);
    if (e.status === "cancelled") lines.push("STATUS:CANCELLED");
    lines.push("END:VEVENT");
    if (withDeadlines && e.status !== "cancelled") {
      for (const r of e.roles) {
        if (!r.closes || Date.parse(r.closes) < Date.parse(now)) continue;
        const end = new Date(new Date(r.closes).getTime()).toISOString();
        const start = new Date(new Date(r.closes).getTime() - 30 * 60_000).toISOString();
        lines.push(
          "BEGIN:VEVENT",
          `UID:${e.id}-${r.role}-deadline@openroster`,
          `DTSTAMP:${utc(e.last_verified)}`,
          `DTSTART:${utc(start)}`,
          `DTEND:${utc(end)}`,
          `SUMMARY:${icsEscape(`Apply by: ${e.title} (${ROLE_LABEL[r.role].toLowerCase()})`)}`,
          `DESCRIPTION:${icsEscape(`Applications close for ${e.title}.\nDetails: ${SITE_URL}/o/${e.id}/`)}`,
          `URL:${r.url ?? `${SITE_URL}/o/${e.id}/`}`,
          "BEGIN:VALARM",
          "ACTION:DISPLAY",
          `DESCRIPTION:${icsEscape(`Applications for ${e.title} close soon`)}`,
          "TRIGGER:-P1D",
          "END:VALARM",
          "END:VEVENT",
        );
      }
    }
  }
  lines.push("END:VCALENDAR");
  return lines.map(fold).join("\r\n") + "\r\n";
}

const xml = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export function toRSS(entries: Entry[], title: string, link: string): string {
  const items = [...entries]
    .sort((a, b) => b.first_seen.localeCompare(a.first_seen))
    .slice(0, 200)
    .map((e) => {
      const url = `${SITE_URL}/o/${e.id}/`;
      const desc = `${TYPE_LABEL[e.type] ?? "Event"} · ${fmtWhen(e)}. ${e.summary}`;
      return `<item><title>${xml(e.title)}</title><link>${url}</link><guid isPermaLink="true">${url}</guid><pubDate>${new Date(e.first_seen).toUTCString()}</pubDate><description>${xml(desc)}</description></item>`;
    })
    .join("");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>${xml(title)}</title><link>${xml(link)}</link><description>${xml(title)} from OpenRoster</description><ttl>360</ttl>${items}</channel></rss>\n`;
}
