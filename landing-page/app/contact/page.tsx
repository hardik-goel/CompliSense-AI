import Link from "next/link";

import ContactForm from "./contact-form";

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://app.complisenseai.com";

export default function ContactPage() {
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
            <Link className="button button-primary" href="/">
              Back to Home
            </Link>
          </div>
        </div>
      </header>

      <section className="legal-hero">
        <div className="container">
          <p className="section-kicker">Contact</p>
          <h1>Talk to CompliSense-AI.</h1>
          <p className="legal-subtitle">
            If you are evaluating DPDP workflows, AI governance operations, vendor compliance reviews, or audit
            readiness systems, we can show how the platform is structured.
          </p>
        </div>
      </section>

      <section className="container contact-layout">
        <div className="legal-content">
          <section className="legal-section">
            <h2>Support</h2>
            <p>Email: support@complisenseai.com</p>
          </section>
          <section className="legal-section">
            <h2>Live Product</h2>
            <p>
              The public website is paired with the live CompliSense-AI product at{" "}
              <a href={appUrl} target="_blank" rel="noreferrer">
                {appUrl}
              </a>
              .
            </p>
          </section>
          <section className="legal-section">
            <h2>Best Fit</h2>
            <p>
              We typically work with startups, SMBs, and mid-market teams that want to replace fragmented compliance
              execution with structured software workflows.
            </p>
          </section>
        </div>
        <ContactForm />
      </section>
    </main>
  );
}
