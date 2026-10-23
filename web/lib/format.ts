// Dates are always shown in the event's own time zone, so the server render and the browser agree.

function parts(iso: string, tz: string, opts: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: tz, ...opts }).format(new Date(iso));
}

export function fmtDate(iso: string | null, tz = "America/Toronto"): string {
  if (!iso) return "";
  return parts(iso, tz, { month: "short", day: "numeric", year: "numeric" });
}

export function fmtDateTime(iso: string | null, tz = "America/Toronto"): string {
  if (!iso) return "";
  return parts(iso, tz, {
    weekday: "short", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit",
    timeZoneName: "short",
  });
}

function dayKey(iso: string, tz: string): string {
  return parts(iso, tz, { year: "numeric", month: "2-digit", day: "2-digit" });
}

export function fmtWhen(o: { start: string; end: string | null; timezone: string; all_day: boolean }): string {
  const tz = o.timezone;
  const sameDay = o.end ? dayKey(o.start, tz) === dayKey(o.end, tz) : true;
  if (o.all_day) {
    const s = parts(o.start, tz, { weekday: "short", month: "short", day: "numeric", year: "numeric" });
    if (o.end && !sameDay) {
      return `${parts(o.start, tz, { weekday: "short", month: "short", day: "numeric" })} – ${parts(o.end, tz, {
        weekday: "short", month: "short", day: "numeric", year: "numeric" })}`;
    }
    return s;
  }
  const start = parts(o.start, tz, {
    weekday: "short", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit",
  });
  const zone = parts(o.start, tz, { timeZoneName: "short" }).split(" ").pop();
  if (!o.end) return `${start} ${zone}`;
  const end = sameDay
    ? parts(o.end, tz, { hour: "numeric", minute: "2-digit" })
    : parts(o.end, tz, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  return `${start} – ${end} ${zone}`;
}

/** Monday (YYYY-MM-DD) of the week containing iso, in Toronto time. */
export function weekOf(iso: string, tz = "America/Toronto"): string {
  const d = new Date(`${dayKey(iso, tz)}T12:00:00Z`);
  const dow = (d.getUTCDay() + 6) % 7;
  d.setUTCDate(d.getUTCDate() - dow);
  return d.toISOString().slice(0, 10);
}
