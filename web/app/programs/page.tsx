// /programs/: the directory filtered to recurring early-career programs (config/programs.yaml).
import type { Metadata } from "next";
import Link from "next/link";
import { ListPage } from "@/components/ListPage";
import { programs } from "@/lib/data";

export const metadata: Metadata = {
  title: "Programs",
  description: "Recurring early-career programs, insight days and fellowships for CS students in Canada.",
};

export default function ProgramsPage() {
  return (
    <ListPage
      title="Recurring programs"
      intro={
        <>
          Insight days, first- and second-year programs and fellowships that come back every year. Dates change each
          cycle, so each one links to its official page. Filter by your year on the left, or see{" "}
          <Link href="/">everything together</Link>.
        </>
      }
      items={[]}
      total={0}
      feedSlug="all"
      baseQuery="type=program"
      staticPrograms={[...programs].sort((a, b) => a.name.localeCompare(b.name))}
    />
  );
}
