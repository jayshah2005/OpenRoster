import { ListPage, PAGE_SIZE } from "@/components/ListPage";
import { liveEntries, programs } from "@/lib/data";

export default function Home() {
  const pages = Math.max(1, Math.ceil(liveEntries.length / PAGE_SIZE));
  return (
    <ListPage
      title="Every CS opportunity in one place"
      hero
      items={liveEntries.slice(0, PAGE_SIZE)}
      total={liveEntries.length}
      page={1}
      pages={pages}
      feedSlug="all"
      staticPrograms={pages === 1 ? programs : []}
    />
  );
}
