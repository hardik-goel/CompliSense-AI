import type { MetadataRoute } from "next";
import { getAllPosts } from "./resources/lib/posts";

const siteUrl = "https://complisenseai.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: siteUrl, lastModified: now, changeFrequency: "weekly", priority: 1.0 },
    { url: `${siteUrl}/resources`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${siteUrl}/showcase`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${siteUrl}/readiness`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${siteUrl}/changelog`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${siteUrl}/demo`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${siteUrl}/about`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${siteUrl}/contact`, lastModified: now, changeFrequency: "monthly", priority: 0.6 },
    { url: `${siteUrl}/privacy`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
    { url: `${siteUrl}/terms`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
  ];

  const postRoutes: MetadataRoute.Sitemap = getAllPosts().map((post) => ({
    url: `${siteUrl}/resources/${post.slug}`,
    lastModified: new Date(post.updated ?? post.date),
    changeFrequency: "monthly",
    priority: 0.7,
  }));

  return [...staticRoutes, ...postRoutes];
}
