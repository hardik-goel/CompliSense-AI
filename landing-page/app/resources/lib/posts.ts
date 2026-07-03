import fs from "fs";
import path from "path";
import matter from "gray-matter";

// Single source of truth for resource articles.
// Content lives as .mdx files in app/resources/_posts (private folder — not routed).
const POSTS_DIR = path.join(process.cwd(), "app", "resources", "_posts");

export interface PostMeta {
  slug: string;
  title: string;
  description: string;
  date: string; // ISO — first published
  updated?: string; // ISO — last substantive edit
  tags: string[];
  author: string;
  published: boolean;
  readingMinutes: number;
}

export interface Post extends PostMeta {
  content: string; // raw MDX body
}

function readingMinutes(body: string): number {
  const words = body.trim().split(/\s+/).length;
  return Math.max(1, Math.round(words / 220));
}

function parseFile(fileName: string): Post {
  const slug = fileName.replace(/\.mdx$/, "");
  const raw = fs.readFileSync(path.join(POSTS_DIR, fileName), "utf8");
  const { data, content } = matter(raw);

  return {
    slug,
    title: String(data.title ?? slug),
    description: String(data.description ?? ""),
    date: String(data.date ?? ""),
    updated: data.updated ? String(data.updated) : undefined,
    tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
    author: String(data.author ?? "CompliSense-AI"),
    published: data.published !== false, // default published unless explicitly false
    readingMinutes: readingMinutes(content),
    content,
  };
}

function allFiles(): string[] {
  if (!fs.existsSync(POSTS_DIR)) return [];
  return fs.readdirSync(POSTS_DIR).filter((f) => f.endsWith(".mdx"));
}

/** All published posts, newest first. */
export function getAllPosts(): Post[] {
  return allFiles()
    .map(parseFile)
    .filter((p) => p.published)
    .sort((a, b) => (a.date < b.date ? 1 : -1));
}

/** Published slugs — for generateStaticParams. */
export function getAllSlugs(): string[] {
  return getAllPosts().map((p) => p.slug);
}

/** One published post by slug, or null. */
export function getPost(slug: string): Post | null {
  const file = `${slug}.mdx`;
  if (!allFiles().includes(file)) return null;
  const post = parseFile(file);
  return post.published ? post : null;
}

/** URL-safe slug for a tag label, e.g. "EU AI Act" -> "eu-ai-act". */
export function tagSlug(tag: string): string {
  return tag
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export interface TagInfo {
  tag: string; // display label
  slug: string; // url slug
  count: number;
}

/** All tags across published posts, with post counts, sorted by count desc. */
export function getAllTags(): TagInfo[] {
  const byLabel = new Map<string, number>();
  for (const post of getAllPosts()) {
    for (const tag of post.tags) {
      byLabel.set(tag, (byLabel.get(tag) ?? 0) + 1);
    }
  }
  return Array.from(byLabel.entries())
    .map(([tag, count]) => ({ tag, slug: tagSlug(tag), count }))
    .sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag));
}

/** Published posts carrying a tag (matched by slug), newest first. Returns label + posts. */
export function getPostsByTag(slug: string): { tag: string; posts: Post[] } | null {
  const posts = getAllPosts().filter((p) => p.tags.some((t) => tagSlug(t) === slug));
  if (posts.length === 0) return null;
  const tag = posts[0].tags.find((t) => tagSlug(t) === slug) ?? slug;
  return { tag, posts };
}
