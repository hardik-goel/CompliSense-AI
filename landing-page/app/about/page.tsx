import Link from "next/link";

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://complisense-ai-backend.onrender.com";

export default function AboutPage() {
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
            <Link className="button button-primary" href="/contact">
              Book Demo
            </Link>
          </div>
        </div>
      </header>

      <section className="legal-hero">
        <div className="container">
          <p className="section-kicker">About</p>
          <h1>Compliance operations for teams that need software, not patchwork.</h1>
          <p className="legal-subtitle">
            CompliSense-AI is an AI-native compliance operating system built to replace scattered documentation,
            spreadsheet tracking, and consulting-heavy workflows with a repeatable operational platform.
          </p>
        </div>
      </section>

      <section className="container legal-grid">
        <aside className="legal-aside">
          <nav>
            <a href="#mission">Mission</a>
            <a href="#platform">Platform</a>
            <a href="#customers">Customers</a>
            <a href="#positioning">Positioning</a>
          </nav>
        </aside>
        <div className="legal-content">
          <section className="legal-section" id="mission">
            <h2>Mission</h2>
            <p>
              Compliance work often breaks down because evidence, policies, vendor reviews, and governance decisions
              live across disconnected tools. CompliSense-AI brings those workflows into one operating layer so teams
              can move from reactive preparation to continuous readiness.
            </p>
          </section>
          <section className="legal-section" id="platform">
            <h2>Platform Scope</h2>
            <p>
              The platform is designed to support DPDP compliance, AI governance, policy management, risk assessments,
              vendor compliance reviews, evidence collection, and audit readiness. It is built for execution, ownership,
              and traceability rather than static record keeping alone.
            </p>
          </section>
          <section className="legal-section" id="customers">
            <h2>Who It Serves</h2>
            <p>
              CompliSense-AI is intended for startups, SMBs, and mid-market businesses that need a credible compliance
              operating system without standing up a large internal compliance technology team.
            </p>
          </section>
          <section className="legal-section" id="positioning">
            <h2>How We Position the Product</h2>
            <p>
              This is software for compliance operations. It helps teams centralize evidence, structure governance,
              assign work, monitor risk, and maintain readiness across internal reviews, customer diligence, and formal
              audit processes.
            </p>
          </section>
        </div>
      </section>
    </main>
  );
}
