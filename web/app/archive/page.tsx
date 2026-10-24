// /archive/: past listings, kept so old links keep working.
import type { Metadata } from "next";
import Link from "next/link";
import { past } from "@/lib/data";
import { fmtDate } from "@/lib/format";

export const metadata: Metadata = { title: "Past opportunities" };

export default function ArchivePage() {
  return (
    <article className="prose">
      <h1>Past opportunities</h1>
      <p>Past listings keep their addresses, so shared links keep working.</p>
      <ul className="agenda-list">
        {past.slice(0, 500).map((o) => (
          <li key={o.id}>
            {fmtDate(o.start, o.timezone)} · <Link href={`/o/${o.id}/`} prefetch={false}>{o.title}</Link> · {o.organizer}
          </li>
        ))}
      </ul>
      {past.length === 0 && <p className="empty">Nothing archived yet.</p>}
    </article>
  );
}
