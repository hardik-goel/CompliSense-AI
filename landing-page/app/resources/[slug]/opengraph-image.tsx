import { ImageResponse } from "next/og";
import { getAllSlugs, getPost } from "../lib/posts";

// Node runtime (not edge) — reads MDX frontmatter via fs at build time.
export const alt = "CompliSense-AI resource guide";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

export default async function OGImage({ params }: { params: { slug: string } }) {
  const post = getPost(params.slug);
  const title = post?.title ?? "CompliSense-AI Resources";
  const tags = post?.tags.slice(0, 3) ?? [];

  return new ImageResponse(
    (
      <div
        style={{
          width: "1200px",
          height: "630px",
          background: "#07111F",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "80px 100px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div style={{
          position: "absolute", top: "-120px", right: "-120px",
          width: "480px", height: "480px", borderRadius: "50%",
          background: "radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)",
          display: "flex",
        }}/>
        <div style={{
          position: "absolute", bottom: "-80px", left: "-80px",
          width: "360px", height: "360px", borderRadius: "50%",
          background: "radial-gradient(circle, rgba(34,211,238,0.08) 0%, transparent 70%)",
          display: "flex",
        }}/>

        {/* Brand row */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "40px" }}>
          <div style={{
            width: "48px", height: "48px", borderRadius: "10px",
            background: "linear-gradient(135deg, #1D4ED8, #0E7490)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "22px", fontWeight: 800, color: "#fff",
          }}>C</div>
          <div style={{ fontSize: "22px", fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.3px" }}>
            CompliSense-AI
          </div>
          <div style={{
            fontSize: "11px", color: "#64748B", marginLeft: "8px",
            border: "1px solid #1B3A5C", padding: "3px 10px", borderRadius: "4px",
            letterSpacing: "1.5px",
          }}>RESOURCES</div>
        </div>

        {/* Post title */}
        <div style={{
          fontSize: title.length > 70 ? "48px" : "58px",
          fontWeight: 800, color: "#F1F5F9",
          lineHeight: 1.12, letterSpacing: "-1px",
          maxWidth: "1000px",
          display: "flex",
        }}>
          {title}
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div style={{ display: "flex", gap: "12px", marginTop: "40px" }}>
            {tags.map((label) => (
              <div key={label} style={{
                fontSize: "16px", color: "#3B82F6",
                border: "1px solid #1B3A5C", padding: "8px 18px",
                borderRadius: "999px", background: "rgba(59,130,246,0.08)",
                display: "flex",
              }}>{label}</div>
            ))}
          </div>
        )}

        <div style={{
          position: "absolute", bottom: "40px", right: "100px",
          fontSize: "14px", color: "#334155",
        }}>complisenseai.com/resources</div>
      </div>
    ),
    { ...size }
  );
}
