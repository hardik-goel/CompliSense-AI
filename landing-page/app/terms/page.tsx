import Link from "next/link";

const appUrl = "https://app.complisenseai.com";

export default function TermsPage() {
  return (
    <main className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" />
          </Link>
          <div className="header-actions">
            <Link className="button button-ghost" href="/privacy">Privacy Policy</Link>
            <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">Launch App &rarr;</a>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "80px 24px 120px" }}>
        <nav style={{ fontSize: "12px", color: "#64748B", marginBottom: "32px" }}>
          <Link href="/" style={{ color: "#3B82F6" }}>Home</Link> / Terms of Service
        </nav>

        <div style={{ marginBottom: "48px", paddingBottom: "32px", borderBottom: "1px solid #1B3A5C" }}>
          <p style={{ fontSize: "11px", letterSpacing: "2px", color: "#3B82F6", marginBottom: "8px" }}>LEGAL</p>
          <h1 style={{ fontSize: "36px", fontWeight: 800, color: "#F1F5F9", marginBottom: "12px" }}>Terms of Service</h1>
          <p style={{ color: "#94A3B8", fontSize: "14px" }}>Last updated: June 2026 &middot; Effective immediately</p>
        </div>

        <div className="legal-content">
          <section style={{ marginTop: "40px" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Acceptance of Terms</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              By accessing or using CompliSense-AI, you agree to be bound by these Terms. If you do not agree, do not use the platform.
            </p>
          </section>

          <section style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Use of the Platform</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              CompliSense-AI is a compliance operations platform. You may use it for lawful business compliance purposes only. You may not reverse-engineer, resell, or misuse the platform or its outputs.
            </p>
          </section>

          <section style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Accounts and Access</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              You are responsible for maintaining the confidentiality of your account credentials. Notify us immediately if you suspect unauthorised access.
            </p>
          </section>

          <section style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Intellectual Property</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              All platform software, rulepacks, templates, and compliance logic are the intellectual property of CompliSense-AI. Your data and documents remain yours.
            </p>
          </section>

          <section style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Limitation of Liability</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              CompliSense-AI provides operational compliance tooling. It does not constitute legal advice. We are not liable for regulatory outcomes resulting from how the platform is used.
            </p>
          </section>

          <section style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Changes to Terms</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              We may update these Terms. Continued use after changes constitutes acceptance. Material changes will be communicated via email or in-app notice.
            </p>
          </section>
        </div>

        <div style={{ marginTop: "64px", padding: "24px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px" }}>
          <p style={{ fontSize: "13px", fontWeight: 600, color: "#F1F5F9", marginBottom: "8px" }}>Questions about these terms?</p>
          <p style={{ fontSize: "13px", color: "#94A3B8" }}>
            Contact us at <a href="mailto:support@complisenseai.com" style={{ color: "#3B82F6" }}>support@complisenseai.com</a> and we'll respond within 48 hours.
          </p>
        </div>
      </div>

      <footer className="site-footer">
        <div className="container">
          <div className="footer-top" style={{ borderBottom: "1px solid #1B3A5C", paddingBottom: "32px", marginBottom: "32px" }}>
            <div className="footer-brand">
              <img src="/logo.png" alt="CompliSense-AI" style={{ height: "36px", marginBottom: "16px", objectFit: "contain" }} />
              <p style={{ fontSize: "14px", color: "#94A3B8" }}>AI-native compliance for modern teams — built for India's regulatory moment, designed for the operators who can't afford to get it wrong.</p>
            </div>
          </div>
          <div className="footer-bottom">
            <span>&copy; 2026 CompliSense-AI &middot; Built in India 🇮🇳</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
