const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://complisense-ai-backend.onrender.com";

const sections = [
  { href: "#why", label: "Why now" },
  { href: "#flow", label: "How it works" },
  { href: "#platform", label: "Platform" },
  { href: "#faq", label: "FAQ" },
];

const primaryActions = [
  { href: `${backendUrl}/`, label: "Login" },
  { href: `${backendUrl}/`, label: "Register" },
  { href: `${backendUrl}/reports`, label: "Open Reports" },
  { href: "mailto:demo@complisense.ai?subject=Request%20Demo", label: "Request Demo" },
];

const capabilities = [
  {
    title: "Local-first evidence collection",
    text: "Run scans inside the client environment so model artefacts, documents, and governance evidence stay under the client’s control.",
  },
  {
    title: "Hosted compliance workspace",
    text: "Use the SaaS dashboard for projects, scan configurations, audit history, and live result review without rebuilding your internal processes.",
  },
  {
    title: "Rule-driven compliance engine",
    text: "Translate regulatory obligations into machine-checkable controls, then map those controls into findings, confidence, risk, and remediation.",
  },
  {
    title: "Cross-jurisdiction expansion path",
    text: "The same engine can evolve from EU AI Act readiness into DPDP, AI governance policies, and internal control frameworks.",
  },
];

const flow = [
  "Create a project in the SaaS workspace and configure a compliance scan.",
  "Download a customized local agent linked to that project and run it against client artefacts.",
  "Review synced findings, status, risk, and remediation in the hosted dashboard.",
];

const proofPoints = [
  { label: "Public SaaS backend", value: "Render" },
  { label: "Persistence layer", value: "MongoDB Atlas" },
  { label: "Client-side scan mode", value: "Local agent" },
  { label: "Current regulatory pack", value: "EU AI Act" },
];

const outcomes = [
  "Show what documentation exists, what is missing, and which controls need action.",
  "Avoid sending sensitive model artefacts to a third-party SaaS by default.",
  "Give founders and compliance teams a demoable workflow instead of a static checklist.",
];

const faqs = [
  {
    q: "Is this only for EU AI Act?",
    a: "No. The current starter pack is EU AI Act-focused, but the product direction supports additional rulepacks like DPDP or internal AI governance controls.",
  },
  {
    q: "Does client data leave their environment?",
    a: "The intended model is local evidence scanning with only selected metadata and findings synced back to the SaaS dashboard.",
  },
  {
    q: "Can I see the live SaaS product from here?",
    a: "Yes. This landing page links directly into the live hosted backend so prospects can move from marketing site to actual product entry points.",
  },
];

export default function HomePage() {
  return (
    <main className="page">
      <header className="topbar">
        <a className="brand" href="#top">
          <span className="brand-mark">C</span>
          <span>CompliSense AI</span>
        </a>
        <nav className="nav">
          {sections.map((section) => (
            <a key={section.href} href={section.href}>
              {section.label}
            </a>
          ))}
        </nav>
        <div className="nav-actions">
          <a className="ghost-button" href={`${backendUrl}/about`} target="_blank" rel="noreferrer">
            About SaaS
          </a>
          <a className="primary-button" href={`${backendUrl}/`} target="_blank" rel="noreferrer">
            Open Live App
          </a>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">Compliance workflow for AI teams</p>
          <h1>EU AI Act readiness with a local agent and a hosted command center.</h1>
          <p className="lede">
            CompliSense AI helps teams collect evidence locally, translate controls into findings, and review scan
            outcomes through a public SaaS interface that is ready for live demos and customer onboarding.
          </p>
          <div className="quick-actions" aria-label="Primary actions">
            {primaryActions.map((action, index) => (
              <a
                key={action.label}
                className={index === 0 ? "quick-chip quick-chip-primary" : "quick-chip"}
                href={action.href}
                target={action.href.startsWith("http") ? "_blank" : undefined}
                rel={action.href.startsWith("http") ? "noreferrer" : undefined}
              >
                {action.label}
              </a>
            ))}
          </div>
          <div className="hero-actions">
            <a className="primary-button" href={`${backendUrl}/`} target="_blank" rel="noreferrer">
              Launch SaaS Dashboard
            </a>
            <a className="secondary-button" href={`${backendUrl}/reports`} target="_blank" rel="noreferrer">
              View Reports Area
            </a>
          </div>
          <div className="signal-row">
            {proofPoints.map((item) => (
              <div key={item.label} className="signal">
                <span className="signal-label">{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </div>
        <div className="hero-panel">
          <div className="status-strip">
            <span className="live-dot" />
            <span>Live backend connected</span>
          </div>
          <div className="panel-stack">
            <article className="mini-panel">
              <span className="mini-label">Public SaaS</span>
              <h2>Hosted on Render</h2>
              <p>Projects, scans, auth, dashboard, reports, and upload endpoints are already exposed publicly.</p>
            </article>
            <article className="mini-panel">
              <span className="mini-label">Client workflow</span>
              <h2>Download agent, run locally, sync findings</h2>
              <p>The website now links directly into the hosted product rather than acting like an isolated brochure.</p>
            </article>
          </div>
        </div>
      </section>

      <section className="section-grid" id="why">
        <article className="feature-intro">
          <p className="eyebrow">Why this matters</p>
          <h2>Most teams cannot prove AI governance quickly enough.</h2>
          <p>
            Procurement reviews, internal risk checks, investor diligence, and regulator questions usually hit before
            the company has a clean evidence trail. CompliSense AI turns that problem into a repeatable operating flow.
          </p>
        </article>
        <div className="grid">
          {capabilities.map((item) => (
            <article key={item.title} className="card">
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-two-column" id="flow">
        <div className="section-copy">
          <p className="eyebrow">How it works</p>
          <h2>One-page story for a founder, buyer, or compliance lead.</h2>
          <ol className="story-list">
            {flow.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
        <div className="journey-card">
          <div className="journey-node">
            <span>1</span>
            <div>
              <strong>Hosted project setup</strong>
              <p>Users start on the SaaS side and configure scans linked to real projects.</p>
            </div>
          </div>
          <div className="journey-node">
            <span>2</span>
            <div>
              <strong>Local evidence execution</strong>
              <p>The generated agent runs where the client’s artefacts already live.</p>
            </div>
          </div>
          <div className="journey-node">
            <span>3</span>
            <div>
              <strong>Hosted findings review</strong>
              <p>Rule outcomes, summaries, and drill-down details can be reviewed from the browser.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-platform" id="platform">
        <div className="platform-header">
          <p className="eyebrow">Platform</p>
          <h2>A sharper front door that leads into the actual product.</h2>
        </div>
        <div className="platform-grid">
          <article className="platform-card">
            <span className="mini-label">Entry points</span>
            <h3>Connect the marketing site to live product surfaces.</h3>
            <ul>
              <li>
                <a href={`${backendUrl}/`} target="_blank" rel="noreferrer">
                  Login
                </a>
              </li>
              <li>
                <a href={`${backendUrl}/`} target="_blank" rel="noreferrer">
                  Register
                </a>
              </li>
              <li>
                <a href={`${backendUrl}/`} target="_blank" rel="noreferrer">
                  Open live dashboard
                </a>
              </li>
              <li>
                <a href={`${backendUrl}/reports`} target="_blank" rel="noreferrer">
                  Open reports view
                </a>
              </li>
              <li>
                <a href={`${backendUrl}/about`} target="_blank" rel="noreferrer">
                  Product about page
                </a>
              </li>
              <li>
                <a href={`${backendUrl}/api/health`} target="_blank" rel="noreferrer">
                  Backend health check
                </a>
              </li>
            </ul>
          </article>
          <article className="platform-card accent-card">
            <span className="mini-label">Expected outcomes</span>
            <ul className="outcome-list">
              {outcomes.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      <section className="section-faq" id="faq">
        <div className="platform-header">
          <p className="eyebrow">FAQ</p>
          <h2>Short answers a prospect should get without booking a call.</h2>
        </div>
        <div className="faq-list">
          {faqs.map((item) => (
            <details key={item.q} className="faq-item">
              <summary>{item.q}</summary>
              <p>{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="closing-panel">
        <div>
          <p className="eyebrow">Ready to use the live system?</p>
          <h2>Go from landing page to working SaaS in one click.</h2>
        </div>
        <div className="hero-actions">
          <a className="primary-button" href={`${backendUrl}/`} target="_blank" rel="noreferrer">
            Open CompliSense SaaS
          </a>
          <a className="secondary-button" href={`${backendUrl}/reports`} target="_blank" rel="noreferrer">
            Open Reports
          </a>
          <a className="ghost-button" href="mailto:demo@complisense.ai?subject=Request%20Demo">
            Request Demo
          </a>
        </div>
      </section>
    </main>
  );
}
