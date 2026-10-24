// Shared layout for the home directory, its extra pages, /programs/ and every facet page: a heading, the filter
// sidebar on the left and the list on the right. The server renders a plain list and browse links (works without
// JavaScript); in the browser, FilterSidebar and Directory take over and filter the full index.
import Link from "next/link";
import { Suspense } from "react";
import { facets, meta, programs, redFlags, schoolById, schools } from "@/lib/data";
import { REGION_LABEL, ROLE_LABEL, TYPE_PLURAL } from "@/lib/labels";
import type { Entry, Program } from "@/lib/types";
import { Card, ProgramCard } from "./Card";
import { Directory } from "./Directory";
import { FilterSidebar, SidebarFallback } from "./FilterSidebar";
import { Icon } from "./Icon";
import { SubscribeLinks } from "./Results";

export const PAGE_SIZE = 100;

type Props = {
  title: string;
  /** The home page shows the larger intro; other pages a compact heading with a link home. */
  hero?: boolean;
  intro?: React.ReactNode;
  items: Entry[];
  total: number;
  page?: number;
  pages?: number;
  feedSlug: string;
  baseQuery?: string;
  /** Programs to include in the server-rendered list (the home page and /programs/). */
  staticPrograms?: Program[];
};

export function ListPage({
  title, hero = false, intro, items, total, page = 1, pages = 1, feedSlug, baseQuery = "", staticPrograms = [],
}: Props) {
  const fx = facets();
  const schoolNames = Object.fromEntries(schools.map((s) => [s.id, s.name]));
  const flags = redFlags();
  const notice = flags.length > 0 && (
    <div className="notice notice-warn">
      <p className="empty-title"><Icon name="alert" size={18} /> No dated listings yet</p>
      <p>
        {flags[0]} <Link href="/status/">See the status page</Link>. The recurring programs below are always here, and
        you can <Link href="/contribute/">add an event</Link> you know about.
      </p>
    </div>
  );
  const browse = [
    { title: "Type", items: [...fx.type.map((t) => [`/type/${t}/`, TYPE_PLURAL[t]] as [string, string]), ["/programs/", "Recurring programs"] as [string, string]] },
    { title: "Role", items: fx.role.map((r) => [`/role/${r}/`, ROLE_LABEL[r]] as [string, string]) },
    { title: "Region", items: fx.region.map((r) => [`/region/${r}/`, REGION_LABEL[r] ?? r] as [string, string]) },
    { title: "School", items: fx.school.map((s) => [`/school/${s}/`, schoolById.get(s)?.name ?? s] as [string, string]) },
  ];

  const staticBlock = (
    <>
      <div className="results-bar">
        <p className="result-count">
          {pages > 1 ? `${items.length} of ${total} events` : `${total + staticPrograms.length} listed`}
        </p>
        {total > 0 && <SubscribeLinks staticSlug={feedSlug} />}
      </div>
      {total === 0 && !baseQuery && notice}
      {items.length + staticPrograms.length === 0 ? (
        <div className="empty">
          <p className="empty-title">Nothing here yet.</p>
          <p>New listings arrive with every data refresh. <Link href="/contribute/">Add an event you know about</Link>.</p>
        </div>
      ) : (
        <ul className="cards">
          {items.map((e) => <Card key={e.id} e={e} nowIso={meta.built} />)}
          {staticPrograms.map((p) => <ProgramCard key={p.url + p.name} p={p} />)}
        </ul>
      )}
      {pages > 1 && (
        <nav className="pager" aria-label="Pages">
          {page > 1 && <Link className="button button-quiet" href={page === 2 ? "/" : `/page/${page - 1}/`}>Previous</Link>}
          <span>Page {page} of {pages}</span>
          {page < pages && <Link className="button button-quiet" href={`/page/${page + 1}/`}>Next</Link>}
        </nav>
      )}
    </>
  );

  return (
    <>
      {hero ? (
        <section className="hero">
          <p className="eyebrow">For CS students in Ontario and across Canada</p>
          <h1>{title}</h1>
          <p className="hero-sub">
            {intro ?? (
              <>
                Hackathons, info sessions, career fairs, workshops and early-career programs in one list, plus calls for
                volunteers, mentors and judges. Narrow it down with the filters, and we&apos;ll remember them next time. New here?{" "}
                <Link href="/start/">Read the guide</Link>.
              </>
            )}
          </p>
        </section>
      ) : (
        <section className="page-head">
          <p className="crumbs"><Link href="/">All opportunities</Link></p>
          <h1>{title}</h1>
          {intro && <p className="lede">{intro}</p>}
        </section>
      )}

      <div className="directory">
        <aside className="dir-side" aria-label="Filters">
          <Suspense fallback={<SidebarFallback links={browse} />}>
            <FilterSidebar facets={fx} schoolNames={schoolNames} programs={programs} baseQuery={baseQuery} />
          </Suspense>
        </aside>
        <div className="dir-main">
          <Suspense fallback={staticBlock}>
            <Directory programs={programs} baseQuery={baseQuery} feedSlug={feedSlug} notice={notice}>
              {staticBlock}
            </Directory>
          </Suspense>
        </div>
      </div>
    </>
  );
}
