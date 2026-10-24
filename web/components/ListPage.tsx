// Shared layout for the home list, its extra pages and every facet page: hero or heading, quick filters, the
// filter form, results (server-rendered list, upgraded by Results when filters are set), pager and browse links.
import Link from "next/link";
import { Suspense } from "react";
import { facets, meta, redFlags, schoolById, schools } from "@/lib/data";
import { REGION_LABEL, ROLE_LABEL, TYPE_PLURAL } from "@/lib/labels";
import type { Entry } from "@/lib/types";
import { CardList } from "./Card";
import { FilterForm, FilterFormFallback } from "./FilterForm";
import { Icon } from "./Icon";
import { Results, SubscribeLinks } from "./Results";

export const PAGE_SIZE = 100;

type Props = {
  title: string;
  /** The home page shows the large hero; facet pages show a compact heading. */
  hero?: boolean;
  intro?: React.ReactNode;
  items: Entry[];
  total: number;
  page?: number;
  pages?: number;
  feedSlug: string;
  baseQuery?: string;
};

// Shortcuts to common views. They are plain links to prebuilt pages, so they work without JavaScript.
const QUICK: [string, string][] = [
  ["/type/hackathon/", "Hackathons"],
  ["/type/info_session/", "Info sessions"],
  ["/type/workshop/", "Workshops"],
  ["/type/career_fair/", "Career fairs"],
  ["/role/volunteer/", "Volunteer"],
  ["/role/mentor/", "Mentor"],
  ["/programs/", "Programs"],
];

export function ListPage({ title, hero = false, intro, items, total, page = 1, pages = 1, feedSlug, baseQuery = "" }: Props) {
  const fx = facets();
  const schoolNames = Object.fromEntries(schools.map((s) => [s.id, s.name]));
  const flags = hero ? redFlags() : [];
  const staticBlock = (
    <>
      <div className="results-bar">
        <p className="result-count">{pages > 1 ? `${items.length} of ${total} listed` : `${total} listed`}</p>
        <SubscribeLinks staticSlug={feedSlug} />
      </div>
      {total === 0 && flags.length > 0 ? (
        <div className="empty">
          <p className="empty-title"><Icon name="alert" size={18} /> No listings yet</p>
          <p>{flags[0]}</p>
          <p>
            <Link href="/status/">See the status page</Link> for details, browse the{" "}
            <Link href="/programs/">programs directory</Link> in the meantime, or{" "}
            <Link href="/contribute/">add an event</Link>.
          </p>
        </div>
      ) : (
        <CardList items={items} nowIso={meta.built} />
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
                Hackathons, info sessions, career fairs, workshops and early-career programs, plus calls for volunteers,
                mentors and judges. Sorted by the nearest deadline. New here? <Link href="/start/">Read the guide</Link>.
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

      <nav className="quick" aria-label="Quick filters">
        {QUICK.map(([href, label]) => <Link key={href} className="chip" href={href}>{label}</Link>)}
      </nav>

      <Suspense fallback={<FilterFormFallback />}>
        <FilterForm facets={fx} schoolNames={schoolNames} />
      </Suspense>
      <Suspense fallback={staticBlock}>
        <Results baseQuery={baseQuery}>{staticBlock}</Results>
      </Suspense>

      <section className="browse" aria-labelledby="browse-h">
        <h2 id="browse-h">Browse</h2>
        <BrowseRow label="Type" items={fx.type.map((t) => [`/type/${t}/`, TYPE_PLURAL[t]])} />
        <BrowseRow label="Role" items={fx.role.map((r) => [`/role/${r}/`, ROLE_LABEL[r]])} />
        <BrowseRow label="Region" items={fx.region.map((r) => [`/region/${r}/`, REGION_LABEL[r] ?? r])} />
        <BrowseRow label="School" items={fx.school.map((s) => [`/school/${s}/`, schoolById.get(s)?.name ?? s])} />
      </section>
    </>
  );
}

function BrowseRow({ label, items }: { label: string; items: [string, string][] }) {
  if (!items.length) return null;
  return (
    <div className="browse-row">
      <span className="browse-label">{label}</span>
      <div className="chips">
        {items.map(([href, text]) => <Link key={href} className="chip chip-quiet" href={href}>{text}</Link>)}
      </div>
    </div>
  );
}
