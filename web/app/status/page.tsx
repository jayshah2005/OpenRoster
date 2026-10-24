// /status/: where the pipeline stands and any red flags, so an empty or stale site always says why.
// Numbers come from config, data/audit and data/health/state.json (see scripts/gen-data.mjs).
import type { Metadata } from "next";
import Link from "next/link";
import { Icon } from "@/components/Icon";
import { live, meta, redFlags, status } from "@/lib/data";
import { fmtDateTime } from "@/lib/format";
import { REPO_URL } from "@/lib/labels";

export const metadata: Metadata = { title: "Status" };

export default function StatusPage() {
  const flags = redFlags();
  const run = status.lastRun;
  const stats: [string, string | number][] = [
    ["Listings on the site", live.length],
    ["Sources configured", status.configured],
    ["Sources approved", status.approved],
    ["Sources audited", status.audited],
    ["Allowed by their audit", status.verdicts.allowed ?? 0],
    ["Blocked by their audit", status.verdicts.blocked ?? 0],
  ];
  return (
    <article className="prose wide">
      <h1>Status</h1>
      <p className="lede">Where the data pipeline stands. Last site build: {fmtDateTime(meta.built)}.</p>

      {flags.length > 0 ? (
        <section className="flags" aria-labelledby="flags-h">
          <h2 id="flags-h"><Icon name="alert" size={18} /> Red flags</h2>
          <ul>{flags.map((f) => <li key={f}>{f}</li>)}</ul>
        </section>
      ) : (
        <p className="ok-note">No red flags. Sources are approved, running and producing listings.</p>
      )}

      <div className="stats">
        {stats.map(([label, value]) => (
          <div key={label} className="stat">
            <span className="stat-value">{value}</span>
            <span className="stat-label">{label}</span>
          </div>
        ))}
      </div>

      <h2>Last scrape</h2>
      {run ? (
        <p>
          On {run.last_run}: {run.runnable} sources ran, {run.failing} failed, {run.listings} listings were kept and{" "}
          {run.held_for_review} items are waiting for a person to check their dates.
        </p>
      ) : (
        <p>No scrape has produced data yet.</p>
      )}
      {status.failing.length > 0 && (
        <>
          <h3>Sources that failed</h3>
          <ul>{status.failing.map((s) => <li key={s.id}><code>{s.id}</code>: {s.error}</li>)}</ul>
        </>
      )}

      <h2>How a source gets here</h2>
      <p>
        Every source is audited (robots.txt and terms of use) and then approved by a maintainer before it is collected.
        The full audit is in <a href={`${REPO_URL}/blob/main/reports/source-audit.md`}>reports/source-audit.md</a>, and
        problems open <a href={`${REPO_URL}/issues?q=label%3Ahealth`}>health issues</a> on GitHub. Know a source we are
        missing? <Link href="/contribute/">Tell us</Link>.
      </p>
    </article>
  );
}
