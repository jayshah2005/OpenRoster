import type { Metadata } from "next";
import Link from "next/link";
import { programs } from "@/lib/data";
import { REPO_URL } from "@/lib/labels";

export const metadata: Metadata = {
  title: "Programs",
  description: "Recurring early-career programs, fellowships and scholarships for CS students in Canada.",
};

const YEAR = ["High school", "First year", "Second year", "Third year", "Fourth year"];

function years(ys: number[]): string {
  if (!ys.length) return "Any year (check the details)";
  return ys.map((y) => YEAR[y] ?? `Year ${y}`).join(", ");
}

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
      <ul className="programs">
        {sorted.map((p) => (
          <li key={p.url + p.name} className="card">
            <h2 className="card-title">
              <a href={p.url} rel="noopener">{p.name}</a>
            </h2>
            <p className="card-meta">
              {p.organization && <span>{p.organization}</span>}
              <span>For: {years(p.years)}</span>
              {p.timing && <span>When: {p.timing}</span>}
            </p>
            <p>{p.who}</p>
            {p.notes && <p className="muted">{p.notes}</p>}
            <p className="muted small">Details checked {p.checked}. Confirm dates and eligibility on the official page.</p>
          </li>
        ))}
      </ul>
      <p>
        Know a program that belongs here? <a href={`${REPO_URL}/issues/new?template=submit-opportunity.yml`}>Suggest it</a>{" "}
        or see <Link href="/contribute/">other ways to help</Link>.
      </p>
    </article>
  );
}
