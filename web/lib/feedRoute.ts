// Shared handler for /api/feed.ics and /api/feed.rss.
import { liveEntries } from "./data";
import { applyFilters, describe, parseFilters } from "./filter";
import { toICS, toRSS } from "./feeds";
import { ROLE_LABEL, SITE_URL, TYPE_LABEL } from "./labels";

// The only request-time code on the site. Responses are cached by Vercel's CDN per full URL for 6 hours
// (stale-while-revalidate for a day), so each distinct filter costs a handful of invocations per day.
const CACHE = "public, max-age=3600, s-maxage=21600, stale-while-revalidate=86400";

export function feedResponse(req: Request, format: "ics" | "rss"): Response {
  const url = new URL(req.url);
  const f = parseFilters(url.searchParams);
  const items = applyFilters(liveEntries, f, new Date());
  const name = describe(f, { type: TYPE_LABEL, role: ROLE_LABEL });
  if (format === "ics") {
    const deadlines = url.searchParams.get("deadlines") !== "0";
    return new Response(toICS(items, name, { deadlines }), {
      headers: { "content-type": "text/calendar; charset=utf-8", "cache-control": CACHE },
    });
  }
  const page = `${SITE_URL}/?${url.searchParams.toString()}`;
  return new Response(toRSS(items, `OpenRoster: ${name}`, page), {
    headers: { "content-type": "application/rss+xml; charset=utf-8", "cache-control": CACHE },
  });
}
