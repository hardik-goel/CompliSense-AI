import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import { notFound } from "next/navigation";
import { getAllTags, getPostsByTag } from "../../lib/posts";

const siteUrl = "https://complisenseai.com";
const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://app.complisenseai.com";

export function generateStaticParams() {
  return getAllTags().map((t) => ({ tag: t.slug }));
}

export function generateMetadata({ params }: { params: { tag: string } }): Metadata {
  const result = getPostsByTag(params.tag);
  if (!result) return { title: "Not found" };

  const title = `${result.tag} — CompliSense-AI Resources`;
  const description = `Compliance guides tagged ${result.tag}: ${result.posts
    .map((p) => p.title)
    .slice(0, 3)
    .join("; ")}.`;
  const url = `${siteUrl}/resources/tags/${params.tag}`;

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { title, description, url, siteName: "CompliSense-AI", type: "website" },
    twitter: { card: "summary_large_image", title, description },
  };
}

function formatDate(iso: string): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" });
}

export default function TagPage({ params }: { params: { tag: string } }) {
  const result = getPostsByTag(params.tag);
  if (!result) notFound();
  const { tag, posts } = result;

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: siteUrl },
      { "@type": "ListItem", position: 2, name: "Resources", item: `${siteUrl}/resources` },
      { "@type": "ListItem", position: 3, name: tag, item: `${siteUrl}/resources/tags/${params.tag}` },
    ],
  };

  return (
    <main className="legal-page">
      <Script id="tag-breadcrumb-schema" type="application/ld+json">
        {JSON.stringify(breadcrumbSchema)}
      </Script>

      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" style={{ height: "40px" }} />
          </Link>
          <div className="header-actions">
            <a className="button button-ghost" href={appUrl} target="_blank" rel="noreferrer">
              Launch App
            </a>
            <Link className="button button-primary" href="/contact">
              Book Demo
            </Link>
          </div>
        </div>
      </header>

      <section className="legal-hero">
        <div className="container">
          <p className="section-kicker">
            <Link href="/resources" style={{ color: "inherit" }}>
              Resources
            </Link>{" "}
            / Tag
          </p>
          <h1>{tag}</h1>
          <p className="legal-subtitle">
            {posts.length} {posts.length === 1 ? "guide" : "guides"} tagged &ldquo;{tag}&rdquo;.
          </p>
        </div>
      </section>

      <section className="container">
        <div className="resource-grid">
          {posts.map((post) => (
            <Link key={post.slug} href={`/resources/${post.slug}`} className="resource-card">
              <div className="resource-card-tags">
                {post.tags.slice(0, 3).map((t) => (
                  <span key={t} className="resource-tag">
                    {t}
                  </span>
                ))}
              </div>
              <h2 className="resource-card-title">{post.title}</h2>
              <p className="resource-card-desc">{post.description}</p>
              <div className="resource-card-meta">
                <time dateTime={post.date}>{formatDate(post.date)}</time>
                <span aria-hidden="true">·</span>
                <span>{post.readingMinutes} min read</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
