import { getAllPosts } from "../lib/posts";

// Static RSS 2.0 feed for the resources hub, generated at build time.
export const dynamic = "force-static";

const siteUrl = "https://complisenseai.com";
const feedUrl = `${siteUrl}/resources/feed.xml`;

function escapeXml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function GET() {
  const posts = getAllPosts();
  const lastBuild = posts[0] ? new Date(posts[0].updated ?? posts[0].date) : new Date(0);

  const items = posts
    .map((post) => {
      const url = `${siteUrl}/resources/${post.slug}`;
      const pubDate = new Date(post.date).toUTCString();
      const categories = post.tags
        .map((t) => `      <category>${escapeXml(t)}</category>`)
        .join("\n");
      return `    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <description>${escapeXml(post.description)}</description>
      <pubDate>${pubDate}</pubDate>
      <author>support@complisenseai.com (${escapeXml(post.author)})</author>
${categories}
    </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CompliSense-AI Resources</title>
    <link>${siteUrl}/resources</link>
    <description>Practical guides on DPDP, the EU AI Act, and operational compliance for startups and mid-market teams.</description>
    <language>en</language>
    <lastBuildDate>${lastBuild.toUTCString()}</lastBuildDate>
    <atom:link href="${feedUrl}" rel="self" type="application/rss+xml"/>
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
}
