// /programs/: recurring early-career programs from config/programs.yaml.
import type { Metadata } from "next";
import Link from "next/link";
import { ProgramList } from "@/components/ProgramList";
import { programs } from "@/lib/data";
import { REPO_URL } from "@/lib/labels";

export const metadata: Metadata = {
  title: "Programs",
  description: "Recurring early-career programs, fellowships and scholarships for CS students in Canada.",
};

// Directory of programs that come back every year (config/programs.yaml). Unlike listings, these have no fixed
// date here: each entry says roughly when it opens and links to the official page.
export default function ProgramsPage() {
  const sorted = [...programs].sort((a, b) => (a.years[0] ?? 9) - (b.years[0] ?? 9) || a.name.localeCompare(b.name));
  return (
    <article>
      <h1>Programs</h1>
      <p className="lede">
        Programs that come back every year: insight days, first- and second-year programs, fellowships, student
        ambassador programs and scholarships. Dates change each cycle, so each one links to its official page. When a
        program posts a dated event or deadline, it also shows up in the <Link href="/type/early_career_program/">main list</Link>.
      </p>
      <ProgramList programs={sorted} />
      <p>
        Know a program that belongs here? <a href={`${REPO_URL}/issues/new?template=submit-opportunity.yml`}>Suggest it</a>{" "}
        or see <Link href="/contribute/">other ways to help</Link>.
      </p>
    </article>
  );
}
