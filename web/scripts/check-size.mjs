// Fails if the home page's first load (HTML + CSS + JS, data excluded) exceeds the budget when gzipped.
// Usage: node scripts/check-size.mjs [baseUrl]   (needs `next start` or a deployed URL)
import { gzipSync } from "node:zlib";

const base = (process.argv[2] ?? "http://localhost:3123").replace(/\/$/, "");
const BUDGET = 300 * 1024;
const get = async (u) => Buffer.from(await (await fetch(new URL(u, base))).arrayBuffer());

const html = await get("/");
const assets = [...html.toString().matchAll(/(?:src|href)="(\/_next\/static\/[^"]+\.(?:js|css))"/g)].map((m) => m[1]);
let total = gzipSync(html, { level: 9 }).length;
for (const a of new Set(assets)) total += gzipSync(await get(a), { level: 9 }).length;
const kb = (total / 1024).toFixed(1);
console.log(`first load: ${kb} kB gzipped (${new Set(assets).size} assets), budget ${BUDGET / 1024} kB`);
if (total > BUDGET) process.exit(1);
