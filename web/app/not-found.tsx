import Link from "next/link";

export default function NotFound() {
  return (
    <article className="prose">
      <h1>Not found</h1>
      <p>
        This page doesn&apos;t exist, or the listing was removed. <Link href="/">See all opportunities</Link>.
      </p>
    </article>
  );
}
