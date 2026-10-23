import type { Metadata } from "next";
import { ListPage } from "@/components/ListPage";
import { baseQueryFor, facetTitle, facetValues, selectFacet } from "@/lib/facetPages";

export function generateStaticParams() {
  return facetValues("role").map((value) => ({ value }));
}

export async function generateMetadata({ params }: PageProps<"/role/[value]">): Promise<Metadata> {
  return { title: facetTitle("role", (await params).value) };
}

export default async function Page({ params }: PageProps<"/role/[value]">) {
  const { value } = await params;
  const items = selectFacet("role", value);
  return (
    <ListPage
      title={facetTitle("role", value)}
      items={items}
      total={items.length}
      feedSlug={`role-${value}`}
      baseQuery={baseQueryFor("role", value)}
    />
  );
}
