import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import { getAllSlugs, getPost, tagSlug } from "../lib/posts";

const siteUrl = "https://complisenseai.com";
const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://app.complisenseai.com";

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const post = getPost(params.slug);
  if (!post) return { title: "Not found" };

  const url = `${siteUrl}/resources/${post.slug}`;
  return {
    title: `${post.title} — CompliSense-AI`,
    description: post.description,
    keywords: post.tags,
    authors: [{ name: post.author }],
    alternates: { canonical: url },
    openGraph: {
      title: post.title,
      description: post.description,
      url,
      siteName: "CompliSense-AI",
      type: "article",
      publishedTime: post.date,
      modifiedTime: post.updated ?? post.date,
      authors: [post.author],
      tags: post.tags,
      // og:image comes from the colocated opengraph-image.tsx (per-post) via file convention.
    },
    twitter: { card: "summary_large_image", title: post.title, description: post.description },
  };
}

function formatDate(iso: string): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" });
}

export default function ResourcePost({ params }: { params: { slug: string } }) {
  const post = getPost(params.slug);
  if (!post) notFound();

  const url = `${siteUrl}/resources/${post.slug}`;

  const articleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": `${url}/#article`,
    headline: post.title,
    description: post.description,
    datePublished: post.date,
    dateModified: post.updated ?? post.date,
    author: { "@type": "Organization", name: post.author, url: siteUrl },
    publisher: { "@id": `${siteUrl}/#organization` },
    mainEntityOfPage: { "@type": "WebPage", "@id": url },
    keywords: post.tags.join(", "),
  };

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: siteUrl },
      { "@type": "ListItem", position: 2, name: "Resources", item: `${siteUrl}/resources` },
      { "@type": "ListItem", position: 3, name: post.title, item: url },
    ],
  };

  return (
    <main className="legal-page">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
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

      <article className="container resource-article">
        <nav className="resource-crumbs" aria-label="Breadcrumb">
          <Link href="/resources">Resources</Link>
          <span aria-hidden="true">/</span>
          <span>{post.title}</span>
        </nav>

        <header className="resource-article-head">
          <div className="resource-card-tags">
            {post.tags.map((tag) => (
              <Link key={tag} href={`/resources/tags/${tagSlug(tag)}`} className="resource-tag resource-tag-link">
                {tag}
              </Link>
            ))}
          </div>
          <h1>{post.title}</h1>
          <div className="resource-card-meta">
            <span>By {post.author}</span>
            <span aria-hidden="true">·</span>
            <time dateTime={post.date}>{formatDate(post.date)}</time>
            <span aria-hidden="true">·</span>
            <span>{post.readingMinutes} min read</span>
          </div>
        </header>

        <div className="prose">
          <MDXRemote source={post.content} />
        </div>

        <footer className="resource-article-cta">
          <p>See where your compliance programme stands today — free, no account needed.</p>
          <Link className="button button-primary" href="/readiness">
            Run the readiness check
          </Link>
        </footer>
      </article>
    </main>
  );
}
