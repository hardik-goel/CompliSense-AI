import type { Metadata } from "next";
import ProductShowcase from "../components/ProductShowcase";

export const metadata: Metadata = {
  title: "CompliSense-AI — Product Showcase",
  description: "Self-running product tour: connect, scan, review, export.",
  robots: { index: false, follow: false },
};

// Clean, full-screen canvas with no nav/footer — built for a crisp screen recording.
export default function ShowcaseCapturePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "28px",
        padding: "48px 24px",
        background:
          "radial-gradient(1200px 600px at 50% -10%, rgba(37,99,235,0.18), transparent 60%), var(--bg)",
      }}
    >
      <img src="/logo.png" alt="CompliSense-AI" style={{ height: "44px", objectFit: "contain" }} />
      <div style={{ width: "100%", maxWidth: "880px" }}>
        <ProductShowcase showCaption={false} />
      </div>
      <p style={{ fontSize: "13px", color: "var(--text-muted)", letterSpacing: "1px" }}>
        Compliance Intelligence. Delivered.
      </p>
    </main>
  );
}
