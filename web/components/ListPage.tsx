// Shared layout for the home list, its extra pages and every facet page: filters, results, pager, browse links.
import Link from "next/link";
import { Suspense } from "react";
import { facets, meta, schoolById, schools } from "@/lib/data";
import { REGION_LABEL, ROLE_LABEL, TYPE_PLURAL } from "@/lib/labels";
import type { Entry } from "@/lib/types";
import { CardList } from "./Card";
import { FilterForm, FilterFormFallback } from "./FilterForm";
import { Results, SubscribeLinks } from "./Results";

export const PAGE_SIZE = 100;

type Props = {
  title: string;
  intro?: React.ReactNode;
  items: Entry[];
  total: number;
  page?: number;
  pages?: number;
  feedSlug: string;
  baseQuery?: string;
};

export function ListPage({ title, intro, items, total, page = 1, pages = 1, feedSlug, baseQuery = "" }: Props) {
  const fx = facets();
  const schoolNames = Object.fromEntries(schools.map((s) => [s.id, s.name]));
  const staticBlock = (
    <>
      <p className="result-count">
        {pages > 1 ? `${items.length} of ${total} listed` : `${total} listed`}
      </p>
      <CardList items={items} nowIso={meta.built} />
      {pages > 1 && (
        <nav className="pager" aria-label="Pages">
          {page > 1 && <Link href={page === 2 ? "/" : `/page/${page - 1}/`}>← Previous</Link>}
          <span>Page {page} of {pages}</span>
          {page < pages && <Link href={`/page/${page + 1}/`}>Next →</Link>}
        </nav>
      )}
      <SubscribeLinks staticSlug={feedSlug} />
    </>
  );
  return (
    <>
      <section className="intro">
        <h1>{title}</h1>
        <p>
          {intro ?? (
            <>
              Hackathons, info sessions, career fairs, workshops and early-career programs for CS students, plus calls for
              volunteers, mentors and judges. The nearest application deadline is first. New here?{" "}
              <Link href="/start/">Start with the guide</Link>.
            </>
          )}
        </p>
      </section>
      <Suspense fallback={<FilterFormFallback />}>
        <FilterForm facets={fx} schoolNames={schoolNames} />
      </Suspense>
      <Suspense fallback={staticBlock}>
        <Results baseQuery={baseQuery}>{staticBlock}</Results>
      </Suspense>
      <section className="browse" aria-labelledby="browse-h">
        <h2 id="browse-h">Browse</h2>
        <p><strong>By type:</strong> {fx.type.map((t, i) => <span key={t}>{i > 0 && " · "}<Link href={`/type/${t}/`}>{TYPE_PLURAL[t]}</Link></span>)}</p>
        <p><strong>By role:</strong> {fx.role.map((r, i) => <span key={r}>{i > 0 && " · "}<Link href={`/role/${r}/`}>{ROLE_LABEL[r]}</Link></span>)}</p>
        <p><strong>By region:</strong> {fx.region.map((r, i) => <span key={r}>{i > 0 && " · "}<Link href={`/region/${r}/`}>{REGION_LABEL[r] ?? r}</Link></span>)}</p>
        <p><strong>By school:</strong> {fx.school.map((s, i) => <span key={s}>{i > 0 && " · "}<Link href={`/school/${s}/`}>{schoolById.get(s)?.name ?? s}</Link></span>)}</p>
      </section>
    </>
  );
}
