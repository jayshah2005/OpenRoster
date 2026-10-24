// /page/<n>/: further pages of the main list for browsing without JavaScript.
import { notFound } from "next/navigation";
import { ListPage, PAGE_SIZE } from "@/components/ListPage";
import { liveEntries, programs } from "@/lib/data";

const pageCount = () => Math.max(1, Math.ceil(liveEntries.length / PAGE_SIZE));

export function generateStaticParams() {
  // ensureStatic needs at least one param set; page 2 exists only once there are >100 listings.
  const n = pageCount();
  return n > 1 ? Array.from({ length: n - 1 }, (_, i) => ({ n: String(i + 2) })) : [{ n: "2" }];
}

export default async function Page({ params }: PageProps<"/page/[n]">) {
  const n = Number((await params).n);
  const pages = pageCount();
  if (!Number.isInteger(n) || n < 2 || n > pages) notFound();
  return (
    <ListPage
      title="Upcoming opportunities"
      items={liveEntries.slice((n - 1) * PAGE_SIZE, n * PAGE_SIZE)}
      total={liveEntries.length}
      page={n}
      pages={pages}
      feedSlug="all"
      staticPrograms={n === pages ? programs : []}
    />
  );
}
