// /region/<CA-ON>/: listings in one province or state (same page shape as the home list).
import type { Metadata } from "next";
import { ListPage } from "@/components/ListPage";
import { baseQueryFor, facetTitle, facetValues, selectFacet } from "@/lib/facetPages";

export function generateStaticParams() {
  return facetValues("region").map((value) => ({ value }));
}

export async function generateMetadata({ params }: PageProps<"/region/[value]">): Promise<Metadata> {
  return { title: facetTitle("region", (await params).value) };
}

export default async function Page({ params }: PageProps<"/region/[value]">) {
  const { value } = await params;
  const items = selectFacet("region", value);
  return (
    <ListPage
      title={facetTitle("region", value)}
      items={items}
      total={items.length}
      feedSlug={`region-${value}`}
      baseQuery={baseQueryFor("region", value)}
    />
  );
}
