// /also-useful/: links to internship and new grad lists (config/also_useful.yaml).
import type { Metadata } from "next";
import Link from "next/link";
import { alsoUseful } from "@/lib/data";

export const metadata: Metadata = { title: "Internship lists" };

export default function AlsoUsefulPage() {
  return (
    <article className="prose">
      <h1>Internship and new grad lists</h1>
      <p>
        OpenRoster lists events and programs, not ordinary job postings. For internships and new grad roles, these
        community lists are kept up to date. Many companies on them also run the info sessions and programs you can find
        in our <Link href="/">list</Link> and <Link href="/programs/">programs directory</Link>.
      </p>
      <ul className="link-list">
        {alsoUseful.map((l) => (
          <li key={l.url}>
            <a href={l.url} rel="noopener">{l.name}</a>: {l.description}
          </li>
        ))}
      </ul>
    </article>
  );
}
