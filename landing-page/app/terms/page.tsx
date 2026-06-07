import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="legal-page">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" style={{ height: "40px" }} />
          </Link>
          <div className="header-actions">
            <Link className="button button-ghost" href="/privacy">
              Privacy
            </Link>
            <Link className="button button-primary" href="/contact">
              Contact
            </Link>
          </div>
        </div>
      </header>

      <section className="legal-hero">
        <div className="container">
          <p className="section-kicker">Terms of Service</p>
          <h1>Terms for using the CompliSense-AI website.</h1>
          <p className="legal-subtitle">
            These terms govern use of the public website and related informational materials. Product-specific
            commercial terms may be governed separately in customer agreements.
          </p>
        </div>
      </section>

      <section className="container legal-grid">
        <aside className="legal-aside">
          <nav>
            <a href="#use">Permitted Use</a>
            <a href="#content">Content</a>
            <a href="#disclaimer">Disclaimer</a>
            <a href="#liability">Liability</a>
            <a href="#contact">Contact</a>
          </nav>
        </aside>
        <div className="legal-content">
          <section className="legal-section" id="use">
            <h2>Permitted Use</h2>
            <p>
              You may use the website to learn about CompliSense-AI, request a demo, contact our team, and access
              publicly available information about the platform. You may not misuse the site, interfere with its
              operation, or attempt unauthorized access to connected systems.
            </p>
          </section>
          <section className="legal-section" id="content">
            <h2>Content and Intellectual Property</h2>
            <p>
              Website content, design elements, branding, and related materials are owned by CompliSense-AI or used
              with permission. They may not be copied, redistributed, or reused beyond ordinary evaluative business use
              without prior authorization.
            </p>
          </section>
          <section className="legal-section" id="disclaimer">
            <h2>Website Disclaimer</h2>
            <p>
              Information on the public website is provided for general business and product information purposes. It is
              not legal advice, and using the website does not create a legal advisory relationship.
            </p>
          </section>
          <section className="legal-section" id="liability">
            <h2>Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, CompliSense-AI is not liable for indirect, incidental, special,
              or consequential damages arising from use of or inability to use the public website or its informational
              content.
            </p>
          </section>
          <section className="legal-section" id="contact">
            <h2>Contact</h2>
            <p>Questions about these terms may be directed to support@complisenseai.com.</p>
          </section>
        </div>
      </section>
    </main>
  );
}
