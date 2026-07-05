import type { Metadata } from "next";
import Link from "next/link";
import { getAllPosts, getAllTags } from "./lib/posts";

const siteUrl = "https://complisenseai.com";
const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://app.complisenseai.com";

const title = "Resources — Compliance Guides for DPDP & the EU AI Act";
const description =
  "Practical, no-fluff guides on DPDP readiness, EU AI Act compliance, and building operational compliance programmes for startups and mid-market teams.";

export const metadata: Metadata = {
  title,
  description,
  alternates: {
    canonical: `${siteUrl}/resources`,
    types: { "application/rss+xml": `${siteUrl}/resources/feed.xml` },
  },
  openGraph: {
    title,
    description,
    url: `${siteUrl}/resources`,
    siteName: "CompliSense-AI",
    type: "website",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "CompliSense-AI Resources" }],
  },
  twitter: { card: "summary_large_image", title, description, images: ["/twitter-image"] },
};

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" });
}

export default function ResourcesPage() {
  const posts = getAllPosts();
  const tags = getAllTags();

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: siteUrl },
      { "@type": "ListItem", position: 2, name: "Resources", item: `${siteUrl}/resources` },
    ],
  };

  return (
    <main className="legal-page">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

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
          <p className="section-kicker">Resources</p>
          <h1>Compliance guides, without the consulting markup.</h1>
          <p className="legal-subtitle">
            Practical walkthroughs of the frameworks we build for — DPDP, the EU AI Act, and the operational habits
            that keep a compliance programme current between audits.
          </p>
        </div>
      </section>

      {tags.length > 0 && (
        <section className="container">
          <div className="resource-tagcloud">
            {tags.map((t) => (
              <Link key={t.slug} href={`/resources/tags/${t.slug}`} className="resource-tag resource-tag-link">
                {t.tag} <span className="resource-tag-count">{t.count}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="container">
        <div className="resource-grid">
          {posts.length === 0 && <p className="legal-subtitle">New guides are on the way.</p>}
          {posts.map((post) => (
            <Link key={post.slug} href={`/resources/${post.slug}`} className="resource-card">
              <div className="resource-card-tags">
                {post.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="resource-tag">
                    {tag}
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
