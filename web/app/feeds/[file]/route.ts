import { meta } from "@/lib/data";
import { toICS, toRSS } from "@/lib/feeds";
import { SITE_URL } from "@/lib/labels";
import { prebuiltFeeds } from "@/lib/prebuilt";

// Static feed files, generated at build time: /feeds/<slug>.ics and /feeds/<slug>.rss
export function generateStaticParams() {
  return [...prebuiltFeeds().keys()].flatMap((slug) => [{ file: `${slug}.ics` }, { file: `${slug}.rss` }]);
}

export async function GET(_req: Request, ctx: RouteContext<"/feeds/[file]">) {
  const { file } = await ctx.params;
  const m = /^(.+)\.(ics|rss)$/.exec(file);
  const items = m ? prebuiltFeeds().get(m[1]) : undefined;
  if (!m || !items) return new Response("Not found", { status: 404 });
  const name = m[1].replace("--", " · ");
  if (m[2] === "ics") {
    return new Response(toICS(items, name, { now: meta.built }), { headers: { "content-type": "text/calendar; charset=utf-8" } });
  }
  return new Response(toRSS(items, `OpenRoster: ${name}`, `${SITE_URL}/`), {
    headers: { "content-type": "application/rss+xml; charset=utf-8", "x-built": meta.built },
  });
}
