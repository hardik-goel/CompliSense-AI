import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" style={{ height: "40px" }} />
          </Link>
          <div className="header-actions">
            <Link className="button button-ghost" href="/terms">
              Terms
            </Link>
            <Link className="button button-primary" href="/contact">
              Contact
            </Link>
          </div>
        </div>
      </header>

      <section className="legal-hero">
        <div className="container">
          <p className="section-kicker">Privacy Policy</p>
          <h1>How CompliSense-AI handles website and business information.</h1>
          <p className="legal-subtitle">
            This policy explains the information we collect through the public website, how it is used, and what
            expectations apply when you contact us about the platform.
          </p>
        </div>
      </section>

      <section className="container legal-grid">
        <aside className="legal-aside">
          <nav>
            <a href="#scope">Scope</a>
            <a href="#collection">Information We Collect</a>
            <a href="#use">How We Use Information</a>
            <a href="#sharing">Sharing</a>
            <a href="#rights">Rights</a>
          </nav>
        </aside>
        <div className="legal-content">
          <section className="legal-section" id="scope">
            <h2>Scope</h2>
            <p>
              This policy applies to information submitted through the CompliSense-AI website, direct demo requests,
              and business communications initiated through the public contact channels.
            </p>
          </section>
          <section className="legal-section" id="collection">
            <h2>Information We Collect</h2>
            <p>
              We may collect names, work email addresses, company names, and the contents of messages submitted through
              demo requests or support inquiries. We may also collect routine technical information such as browser
              metadata, referral data, and basic website analytics necessary to operate and improve the site.
            </p>
          </section>
          <section className="legal-section" id="use">
            <h2>How We Use Information</h2>
            <ul>
              <li>Respond to demo requests, support inquiries, and commercial discussions.</li>
              <li>Operate, secure, and improve the public website and related communications.</li>
              <li>Understand demand for product features, workflows, and positioning.</li>
              <li>Maintain business records related to website-originated communications.</li>
            </ul>
          </section>
          <section className="legal-section" id="sharing">
            <h2>Sharing and Disclosure</h2>
            <p>
              We do not sell personal information submitted through the public website. Information may be shared with
              service providers involved in website hosting, analytics, communications, or infrastructure operations
              where reasonably necessary to run the business.
            </p>
          </section>
          <section className="legal-section" id="rights">
            <h2>Data Rights and Contact</h2>
            <p>
              To request access, correction, or deletion of information provided through the website, contact
              support@complisenseai.com. We will review requests in line with applicable law and reasonable business
              recordkeeping needs.
            </p>
          </section>
        </div>
      </section>
    </main>
  );
}
