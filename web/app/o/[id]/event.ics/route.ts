// /o/<id>/event.ics: single-event calendar file for the "Add to calendar" button.
import { allIds, getOpportunity, meta, toEntry } from "@/lib/data";
import { toICS } from "@/lib/feeds";

export function generateStaticParams() {
  const ids = allIds();
  return (ids.length ? ids : ["placeholder"]).map((id) => ({ id }));
}

export async function GET(_req: Request, ctx: RouteContext<"/o/[id]/event.ics">) {
  const { id } = await ctx.params;
  const o = getOpportunity(id);
  if (!o) return new Response("Not found", { status: 404 });
  return new Response(toICS([toEntry(o)], o.title, { now: meta.built }), {
    headers: {
      "content-type": "text/calendar; charset=utf-8",
      "content-disposition": `attachment; filename="${id}.ics"`,
    },
  });
}
