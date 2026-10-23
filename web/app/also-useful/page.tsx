import type { Metadata } from "next";
import { alsoUseful } from "@/lib/data";

export const metadata: Metadata = { title: "Also useful" };

export default function AlsoUsefulPage() {
  return (
    <article className="prose">
      <h1>Also useful</h1>
      <p>OpenRoster doesn&apos;t list ordinary job and internship postings. These trackers do:</p>
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
