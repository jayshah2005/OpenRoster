import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";
import { meta } from "@/lib/data";
import { fmtDateTime } from "@/lib/format";
import { REPO_URL, SITE_NAME, SITE_URL } from "@/lib/labels";
import "./globals.css";

// Every page is generated at build time; the build fails if a page ever needs request-time rendering.
export const ensureStatic = "navigation";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `${SITE_NAME}: opportunities for CS students`, template: `%s · ${SITE_NAME}` },
  description:
    "Hackathons, info sessions, career fairs, workshops and early-career programs for computer science students in Ontario and across Canada, with deadlines first.",
  alternates: { types: { "application/rss+xml": "/feeds/all.rss" } },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#111418" },
  ],
};

// Applies the saved theme before first paint to avoid a flash.
const themeScript = `try{var t=localStorage.getItem("or-theme");if(t)document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <header className="site-header">
          <div className="wrap header-row">
            <Link className="brand" href="/">Open<span>Roster</span></Link>
            <nav aria-label="Main">
              <ul>
                <li><Link href="/">Opportunities</Link></li>
                <li><Link href="/calendar/">Calendar</Link></li>
                <li><Link href="/digest/">This week</Link></li>
                <li><Link href="/programs/">Programs</Link></li>
                <li><Link href="/start/">Start here</Link></li>
                <li><Link href="/contribute/">Contribute</Link></li>
              </ul>
            </nav>
            <ThemeToggle />
          </div>
        </header>
        <main id="main" className="wrap">{children}</main>
        <footer className="site-footer">
          <div className="wrap">
            <p>
              OpenRoster lists the facts and links to each organizer&apos;s page. Listings refresh every 6 hours; last
              update {fmtDateTime(meta.built)}.
            </p>
            <p>
              <Link href="/about/">About</Link> · <Link href="/data/">Data and feeds</Link> ·{" "}
              <Link href="/also-useful/">Internship lists</Link> · <Link href="/archive/">Past events</Link> ·{" "}
              <Link href="/takedown/">Remove a listing</Link> · <a href={REPO_URL}>GitHub</a> ·{" "}
              <a href={`${REPO_URL}/blob/main/LISTINGS.md`}>LISTINGS.md</a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
