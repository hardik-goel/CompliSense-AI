import Link from "next/link";
import type { Metadata } from "next";

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://app.complisenseai.com";
const calendlyUrl = "https://calendly.com/hardik-goel214/complisense-ai";

export const metadata: Metadata = {
  title: "Product Walkthrough — CompliSense-AI",
  description:
    "A complete walkthrough of CompliSense-AI: connect your workspace, run a scan, review findings, and export an audit-ready package.",
};

export default function DemoPage() {
  return (
    <main className="legal-page">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" style={{ height: "40px" }} />
          </Link>
          <div className="header-actions">
            <a className="button button-ghost" href={appUrl} target="_blank" rel="noreferrer">
              Launch App
            </a>
            <a className="button button-primary" href={calendlyUrl} target="_blank" rel="noreferrer">
              Book a Demo
            </a>
          </div>
        </div>
      </header>

      <section className="legal-hero">
        <div className="container">
          <p className="section-kicker">Product Walkthrough</p>
          <h1>See the entire compliance loop, end to end.</h1>
          <p className="legal-subtitle">
            A full walkthrough — connect your workspace, run a scan against live rulepacks, review scored findings,
            and export an audit-ready package. About 4 minutes.
          </p>
        </div>
      </section>

      <section className="container" style={{ paddingBottom: "80px" }}>
        <div
          style={{
            maxWidth: "960px",
            margin: "0 auto",
            borderRadius: "16px",
            overflow: "hidden",
            border: "1px solid #1B3A5C",
            boxShadow: "0 16px 48px rgba(0,0,0,0.35)",
          }}
        >
          <div style={{ position: "relative", paddingBottom: "56.25%", height: 0 }}>
            <iframe
              src="https://www.youtube-nocookie.com/embed/PWvqFBSR6h8?rel=0&modestbranding=1&color=white"
              title="CompliSense-AI — Full product walkthrough"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              loading="lazy"
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                border: "none",
              }}
            />
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: "40px", display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
          <a href={calendlyUrl} target="_blank" rel="noreferrer" className="button button-primary">
            📅 Book a 30-min demo
          </a>
          <a href={appUrl} target="_blank" rel="noreferrer" className="button button-ghost">
            Launch the app &rarr;
          </a>
          <Link href="/" className="button button-ghost">
            &larr; Back to home
          </Link>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container">
          <div className="footer-bottom">
            <span>&copy; 2026 CompliSense-AI &middot; Built in India 🇮🇳</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
