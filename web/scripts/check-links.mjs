// Crawls the running site from "/" and fails if any internal link (page, feed, .ics) does not return 200.
// Usage: node scripts/check-links.mjs [baseUrl]
const base = (process.argv[2] ?? "http://localhost:3123").replace(/\/$/, "");
const LIMIT = 3000;

const seen = new Set(["/"]);
const queue = ["/"];
const broken = [];
let checked = 0;

while (queue.length && checked < LIMIT) {
  const path = queue.shift();
  checked++;
  const res = await fetch(base + path, { redirect: "manual" });
  if (res.status !== 200) {
    broken.push(`${res.status} ${path}`);
    continue;
  }
  if (!(res.headers.get("content-type") ?? "").includes("text/html")) continue;
  const html = await res.text();
  for (const m of html.matchAll(/href="(\/[^"#?]*)(?:[?#][^"]*)?"/g)) {
    const link = m[1];
    if (link.startsWith("/_next/") || link.startsWith("/api/") || seen.has(link)) continue;
    seen.add(link);
    queue.push(link);
  }
}

console.log(`checked ${checked} internal URLs`);
if (broken.length) {
  console.error(`broken links:\n${broken.join("\n")}`);
  process.exit(1);
}
