// IndexNow ping — instantly notifies Bing / Yandex / Seznam of the resource URLs.
// (Google does not use IndexNow; use GSC for Google.)
// Run after publishing a guide:  npm run indexnow
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const KEY = "ad1a7bb325b5364a7a2a3b1969e07904";
const HOST = "complisenseai.com";
const ORIGIN = `https://${HOST}`;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const POSTS_DIR = path.join(__dirname, "..", "app", "resources", "_posts");

function slugToTag(tag) {
  return tag.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function collectUrls() {
  const staticPaths = ["", "/resources", "/showcase", "/readiness", "/about", "/changelog"];
  const urls = new Set(staticPaths.map((p) => `${ORIGIN}${p}`));

  const tags = new Set();
  for (const file of fs.readdirSync(POSTS_DIR).filter((f) => f.endsWith(".mdx"))) {
    const slug = file.replace(/\.mdx$/, "");
    const raw = fs.readFileSync(path.join(POSTS_DIR, file), "utf8");
    // skip drafts
    if (/^published:\s*false\s*$/m.test(raw)) continue;
    urls.add(`${ORIGIN}/resources/${slug}`);
    const tagLine = raw.match(/^tags:\s*\[(.*)\]/m);
    if (tagLine) {
      for (const t of tagLine[1].split(",")) {
        const clean = t.trim().replace(/^["']|["']$/g, "");
        if (clean) tags.add(slugToTag(clean));
      }
    }
  }
  for (const t of tags) urls.add(`${ORIGIN}/resources/tags/${t}`);
  return [...urls];
}

async function main() {
  const urlList = collectUrls();
  const body = {
    host: HOST,
    key: KEY,
    keyLocation: `${ORIGIN}/${KEY}.txt`,
    urlList,
  };

  console.log(`Submitting ${urlList.length} URLs to IndexNow...`);
  const res = await fetch("https://api.indexnow.org/indexnow", {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body: JSON.stringify(body),
  });
  // IndexNow: 200 or 202 = accepted.
  console.log(`IndexNow responded: ${res.status} ${res.statusText}`);
  if (res.status !== 200 && res.status !== 202) {
    console.error(await res.text());
    process.exit(1);
  }
  console.log("Done. URLs submitted:\n" + urlList.map((u) => "  " + u).join("\n"));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
