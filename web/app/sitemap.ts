import type { MetadataRoute } from "next";
import { live, meta } from "@/lib/data";
import { SITE_URL } from "@/lib/labels";

export default function sitemap(): MetadataRoute.Sitemap {
  const fixed = ["", "calendar/", "digest/", "about/", "submit/", "also-useful/"].map((p) => ({
    url: `${SITE_URL}/${p}`,
    lastModified: meta.built,
  }));
  return [...fixed, ...live.map((o) => ({ url: `${SITE_URL}/o/${o.id}/`, lastModified: o.last_verified }))];
}
