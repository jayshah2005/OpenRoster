// /api/feed.ics?<filters>: calendar feed for any filtered view (request-time, CDN-cached; see lib/feedRoute.ts).
import { feedResponse } from "@/lib/feedRoute";

export function GET(req: Request) {
  return feedResponse(req, "ics");
}
