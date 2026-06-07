import type { MetadataRoute } from "next";

const siteUrl = "https://complisenseai.com";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/about", "/contact", "/privacy", "/terms"].map((path) => ({
    url: `${siteUrl}${path}`,
    lastModified: new Date(),
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1 : 0.8,
  }));
}
