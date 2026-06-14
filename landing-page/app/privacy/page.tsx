import Link from "next/link";

const appUrl = "https://app.complisenseai.com";

export default function PrivacyPage() {
  return (
    <main className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" />
          </Link>
          <div className="header-actions">
            <Link className="button button-ghost" href="/terms">Terms</Link>
            <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">Launch App &rarr;</a>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "80px 24px 120px" }}>
        <nav style={{ fontSize: "12px", color: "#64748B", marginBottom: "32px" }}>
          <Link href="/" style={{ color: "#3B82F6" }}>Home</Link> / Privacy Policy
        </nav>

        <div style={{ marginBottom: "48px", paddingBottom: "32px", borderBottom: "1px solid #1B3A5C" }}>
          <p style={{ fontSize: "11px", letterSpacing: "2px", color: "#3B82F6", marginBottom: "8px" }}>LEGAL</p>
          <h1 style={{ fontSize: "36px", fontWeight: 800, color: "#F1F5F9", marginBottom: "12px" }}>Privacy Policy</h1>
          <p style={{ color: "#94A3B8", fontSize: "14px" }}>Last updated: June 2026 &middot; Effective immediately</p>
          <p style={{ color: "#64748B", fontSize: "13px", marginTop: "8px" }}>
            How CompliSense-AI handles website and business information.
          </p>
        </div>

        <div className="legal-content">
          <section id="scope" style={{ marginTop: "40px" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Scope</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              This policy applies to information submitted through the CompliSense-AI website, direct demo requests,
              and business communications initiated through the public contact channels.
            </p>
          </section>
          
          <section id="collection" style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Information We Collect</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              We may collect names, work email addresses, company names, and the contents of messages submitted through
              demo requests or support inquiries. We may also collect routine technical information such as browser
              metadata, referral data, and basic website analytics necessary to operate and improve the site.
            </p>
          </section>
          
          <section id="use" style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>How We Use Information</h2>
            <ul style={{ color: "#94A3B8", paddingLeft: "20px", marginTop: "8px", fontSize: "15px", lineHeight: 1.8 }}>
              <li style={{ marginBottom: "8px" }}>Respond to demo requests, support inquiries, and commercial discussions.</li>
              <li style={{ marginBottom: "8px" }}>Operate, secure, and improve the public website and related communications.</li>
              <li style={{ marginBottom: "8px" }}>Understand demand for product features, workflows, and positioning.</li>
              <li style={{ marginBottom: "8px" }}>Maintain business records related to website-originated communications.</li>
            </ul>
          </section>
          
          <section id="sharing" style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Sharing and Disclosure</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              We do not sell personal information submitted through the public website. Information may be shared with
              service providers involved in website hosting, analytics, communications, or infrastructure operations
              where reasonably necessary to run the business.
            </p>
          </section>
          
          <section id="rights" style={{ marginTop: "40px", paddingTop: "40px", borderTop: "1px solid #1B3A5C" }}>
            <h2 style={{ fontSize: "20px", color: "#F1F5F9", marginBottom: "16px" }}>Data Rights and Contact</h2>
            <p style={{ fontSize: "15px", lineHeight: 1.8, color: "#94A3B8" }}>
              To request access, correction, or deletion of information provided through the website, contact us below. We will review requests in line with applicable law and reasonable business
              recordkeeping needs.
            </p>
          </section>
        </div>

        <div style={{ marginTop: "64px", padding: "24px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px" }}>
          <p style={{ fontSize: "13px", fontWeight: 600, color: "#F1F5F9", marginBottom: "8px" }}>Questions about this policy?</p>
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
