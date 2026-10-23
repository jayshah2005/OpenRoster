import type { Metadata } from "next";
import { ListPage } from "@/components/ListPage";
import { baseQueryFor, facetTitle, facetValues, selectFacet } from "@/lib/facetPages";

export function generateStaticParams() {
  return facetValues("type").map((value) => ({ value }));
}

export async function generateMetadata({ params }: PageProps<"/type/[value]">): Promise<Metadata> {
  return { title: facetTitle("type", (await params).value) };
}

export default async function Page({ params }: PageProps<"/type/[value]">) {
  const { value } = await params;
  const items = selectFacet("type", value);
  return (
    <ListPage
      title={facetTitle("type", value)}
      items={items}
      total={items.length}
      feedSlug={`type-${value}`}
      baseQuery={baseQueryFor("type", value)}
    />
  );
}
