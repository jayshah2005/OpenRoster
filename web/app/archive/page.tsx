// /archive/: past listings, kept so old links keep working.
import type { Metadata } from "next";
import { ArchiveList } from "@/components/ArchiveList";
import { past } from "@/lib/data";
import { fmtDate } from "@/lib/format";

export const metadata: Metadata = { title: "Past opportunities" };

export default function ArchivePage() {
  const rows = past.slice(0, 500).map((o) => ({
    id: o.id, title: o.title, organizer: o.organizer, type: o.type,
    date: fmtDate(o.start, o.timezone), year: o.start.slice(0, 4),
  }));
  return (
    <article className="prose wide">
      <h1>Past opportunities</h1>
      <p>Past listings keep their addresses, so shared links keep working.</p>
      {past.length === 0 ? <p className="empty">Nothing archived yet.</p> : <ArchiveList rows={rows} />}
    </article>
  );
}
