import { ListPage, PAGE_SIZE } from "@/components/ListPage";
import { liveEntries } from "@/lib/data";

export default function Home() {
  const pages = Math.max(1, Math.ceil(liveEntries.length / PAGE_SIZE));
  return (
    <ListPage
      title="Upcoming opportunities"
      items={liveEntries.slice(0, PAGE_SIZE)}
      total={liveEntries.length}
      page={1}
      pages={pages}
      feedSlug="all"
    />
  );
}
