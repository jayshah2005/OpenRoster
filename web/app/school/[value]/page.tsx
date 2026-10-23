import type { Metadata } from "next";
import { ListPage } from "@/components/ListPage";
import { baseQueryFor, facetTitle, facetValues, selectFacet } from "@/lib/facetPages";

export function generateStaticParams() {
  return facetValues("school").map((value) => ({ value }));
}

export async function generateMetadata({ params }: PageProps<"/school/[value]">): Promise<Metadata> {
  return { title: facetTitle("school", (await params).value) };
}

export default async function Page({ params }: PageProps<"/school/[value]">) {
  const { value } = await params;
  const items = selectFacet("school", value);
  return (
    <ListPage
      title={facetTitle("school", value)}
      items={items}
      total={items.length}
      feedSlug={`school-${value}`}
      baseQuery={baseQueryFor("school", value)}
    />
  );
}
