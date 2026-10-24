import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";
import { meta } from "@/lib/data";
import { fmtDateTime } from "@/lib/format";
import { REPO_URL, SITE_NAME, SITE_URL } from "@/lib/labels";
import "./globals.css";

// Every page is generated at build time; the build fails if a page ever needs request-time rendering.
export const ensureStatic = "navigation";

// Self-hosted at build time by next/font, so visitors make no requests to Google.
const sans = Geist({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

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
    { media: "(prefers-color-scheme: dark)", color: "#0b0c10" },
  ],
};

// Applies the saved theme before first paint to avoid a flash.
const themeScript = `try{var t=localStorage.getItem("or-theme");if(t)document.documentElement.dataset.theme=t}catch(e){}`;

const NAV: [string, string][] = [
  ["/", "Opportunities"],
  ["/calendar/", "Calendar"],
  ["/digest/", "This week"],
  ["/programs/", "Programs"],
  ["/start/", "Guide"],
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <header className="site-header">
          <div className="wrap header-row">
            <Link className="brand" href="/" aria-label="OpenRoster home">
              <svg className="logo" width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
                <rect width="32" height="32" rx="8" fill="currentColor" />
                <path d="M9 11h14M9 16h14M9 21h8" stroke="var(--bg)" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <span>OpenRoster</span>
            </Link>
            <nav aria-label="Main">
              <ul>
                {NAV.map(([href, label]) => <li key={href}><Link href={href}>{label}</Link></li>)}
              </ul>
            </nav>
            <div className="header-actions">
              <Link className="button button-small" href="/contribute/">Add an event</Link>
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main id="main" className="wrap">{children}</main>
        <footer className="site-footer">
          <div className="wrap footer-grid">
            <div>
              <p className="footer-brand">OpenRoster</p>
              <p className="muted">
                Events and early-career programs for CS students. We list the facts and link to each organizer&apos;s
                page. Updated every 6 hours; last update {fmtDateTime(meta.built)}.
              </p>
            </div>
            <div>
              <p className="footer-head">Explore</p>
              <ul>
                <li><Link href="/programs/">Programs</Link></li>
                <li><Link href="/also-useful/">Internship lists</Link></li>
                <li><Link href="/archive/">Past events</Link></li>
                <li><Link href="/data/">Feeds and data</Link></li>
              </ul>
            </div>
            <div>
              <p className="footer-head">Project</p>
              <ul>
                <li><Link href="/about/">About</Link></li>
                <li><Link href="/contribute/">Contribute</Link></li>
                <li><Link href="/status/">Status</Link></li>
                <li><Link href="/takedown/">Remove a listing</Link></li>
                <li><a href={REPO_URL}>GitHub</a></li>
              </ul>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
