import { feedResponse } from "@/lib/feedRoute";

export function GET(req: Request) {
  return feedResponse(req, "ics");
}
