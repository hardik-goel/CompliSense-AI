import Link from "next/link";

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://app.complisenseai.com";
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.complisenseai.com";
const supportEmail = "support@complisenseai.com";
const demoMailto = `mailto:${supportEmail}?subject=Book%20a%20Demo%20with%20CompliSense-AI`;

const platformHighlights = [
  "DPDP Ready",
  "AI Governance",
  "Audit Trails",
  "Vendor Assessments",
  "Policy Management",
  "Risk Monitoring",
];

const featureCards = [
  {
    title: "DPDP Compliance Automation",
    description:
      "Map obligations to workflows, monitor readiness, and centralize evidence without turning compliance into a spreadsheet exercise.",
    icon: "shield",
  },
  {
    title: "AI Governance Workflows",
    description:
      "Operationalize model governance, accountability, and control documentation across internal teams and external stakeholders.",
    icon: "spark",
  },
  {
    title: "Risk Assessments",
    description:
      "Track open risks, materiality, remediation owners, and review cycles in one operating system built for ongoing compliance.",
    icon: "risk",
  },
  {
    title: "Policy Management",
    description:
      "Keep privacy, security, and AI governance policies versioned, discoverable, and tied to real operational controls.",
    icon: "doc",
  },
  {
    title: "Audit Trails",
    description:
      "Maintain a durable record of scans, changes, approvals, and evidence movement for internal reviews and external audits.",
    icon: "trail",
  },
  {
    title: "Vendor Compliance",
    description:
      "Review third parties with structured workflows, risk signals, and supporting documentation instead of email-based follow-ups.",
    icon: "vendor",
  },
];

const workflowSteps = [
  {
    step: "01",
    title: "Connect",
    description: "Import policies, controls, vendors, and documentation into a single structured workspace.",
  },
  {
    step: "02",
    title: "Automate",
    description: "Generate workflows, evidence collection, reviews, and governance operations around your real compliance program.",
  },
  {
    step: "03",
    title: "Stay Ready",
    description: "Maintain continuous readiness with active monitoring, traceable decisions, and an always-current audit trail.",
  },
];

const metrics = [
  { value: "60%", label: "Reduction in Compliance Effort" },
  { value: "120+", label: "Policies & Records Centralized" },
  { value: "Hours", label: "Instead of Days for Audit Preparation" },
  { value: "8 Weeks", label: "To Operational Readiness" },
];

const securityItems = [
  "Role-Based Access Controls",
  "Audit Logging",
  "Data Governance",
  "Vendor Assessments",
  "Compliance Evidence Collection",
  "Continuous Monitoring",
];

const testimonials = [
  {
    quote:
      "Before CompliSense-AI, compliance lived across spreadsheets and shared drives. Within weeks, we had a centralized workspace, automated workflows, and significantly faster audit readiness.",
    author: "Founder, Multi-City Media Platform",
  },
  {
    quote:
      "As our platform scaled, compliance processes were becoming increasingly difficult to track across teams, vendors, and internal systems. CompliSense-AI helped us standardize governance workflows, centralize evidence collection, and stay audit-ready without adding operational overhead.",
    author: "CEO & Founder, Data & Operations Intelligence Company",
  },
];

const faqItems = [
  {
    question: "What does CompliSense-AI replace?",
    answer:
      "It replaces fragmented compliance operations spread across spreadsheets, shared drives, email threads, and consulting-heavy manual processes.",
  },
  {
    question: "Who is this built for?",
    answer:
      "The platform is designed for startups, SMBs, and mid-market teams that need an operational compliance system without building an internal platform from scratch.",
  },
  {
    question: "How does the platform connect to the live product?",
    answer:
      "The marketing site lives at complisenseai.com, the customer application runs at app.complisenseai.com, and API traffic is isolated at api.complisenseai.com.",
  },
];

function Icon({ kind }: { kind: string }) {
  switch (kind) {
    case "shield":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3l7 3v5c0 4.7-2.7 8.9-7 10-4.3-1.1-7-5.3-7-10V6l7-3z" />
          <path d="M9 12.2l2 2.2 4-4.4" />
        </svg>
      );
    case "spark":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 2l1.7 5.3L19 9l-5.3 1.7L12 16l-1.7-5.3L5 9l5.3-1.7L12 2z" />
          <path d="M18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9L18 15z" />
        </svg>
      );
    case "risk":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 4l8 14H4L12 4z" />
          <path d="M12 9v4" />
          <path d="M12 16h.01" />
        </svg>
      );
    case "doc":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M8 3h6l4 4v14H8z" />
          <path d="M14 3v5h4" />
          <path d="M10 12h6M10 16h6" />
        </svg>
      );
    case "trail":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 6h14M5 12h10M5 18h14" />
          <path d="M17 10l2 2-2 2" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 6h16v12H4z" />
          <path d="M8 10h8M8 14h5" />
        </svg>
      );
  }
}

export default function HomePage() {
  return (
    <main className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.svg" alt="CompliSense-AI" className="brand-logo" />
          </Link>
          <nav className="site-nav" aria-label="Primary navigation">
            <a href="#platform">Platform</a>
            <a href="#solutions">Solutions</a>
            <a href="#pricing">Pricing</a>
            <Link href="/about">About</Link>
            <Link href="/contact">Contact</Link>
          </nav>
          <div className="header-actions">
            <a className="button button-ghost" href={appUrl} target="_blank" rel="noreferrer">
              Launch App
            </a>
            <a className="button button-primary" href={demoMailto}>
              Book Demo
            </a>
          </div>
        </div>
      </header>

      <section className="hero-section">
        <div className="container hero-grid">
          <div className="hero-copy">
            <div className="eyebrow-pill">AI-native compliance operating system</div>
            <h1>AI-Native Compliance. Built for Modern Businesses.</h1>
            <p className="hero-text">
              Automate DPDP compliance, AI governance, policy management, risk assessments, and audit readiness from a
              single platform.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href={demoMailto}>
                Book a Demo
              </a>
              <a className="button button-secondary" href={appUrl} target="_blank" rel="noreferrer">
                Launch App
              </a>
            </div>
            <div className="hero-proof">
              <div>
                <strong>Built for</strong>
                <span>Startups, SMBs, Mid-market</span>
              </div>
              <div>
                <strong>Use cases</strong>
                <span>DPDP, AI governance, vendor reviews</span>
              </div>
              <div>
                <strong>Operating model</strong>
                <span>Continuous compliance, not periodic cleanup</span>
              </div>
            </div>
          </div>

          <div className="hero-visual" aria-label="CompliSense AI dashboard preview">
            <div className="mock-window">
              <div className="mock-window-bar">
                <span />
                <span />
                <span />
              </div>
              <div className="mock-window-body">
                <div className="mock-topline">
                  <div>
                    <p className="mini-label">Command Center</p>
                    <h2>Compliance Operations</h2>
                  </div>
                  <div className="status-badge status-badge-live">Audit Trail Active</div>
                </div>
              <div className="metric-grid">
                  <article className="metric-card metric-card-primary">
                    <span>Compliance Score</span>
                    <strong>94%</strong>
                    <small>Operational baseline is healthy</small>
                  </article>
                  <article className="metric-card">
                    <span>DPDP Readiness</span>
                    <strong>Ready</strong>
                    <small>Controls mapped and evidence linked</small>
                  </article>
                  <article className="metric-card">
                    <span>Policies Managed</span>
                    <strong>128</strong>
                    <small>Versioned and assigned</small>
                  </article>
                  <article className="metric-card">
                    <span>Vendor Assessments</span>
                    <strong>42</strong>
                    <small>Reviews centralized</small>
                  </article>
                  <article className="metric-card">
                    <span>Open Risks</span>
                    <strong>3</strong>
                    <small>Escalated to owners</small>
                  </article>
                  <article className="metric-card">
                    <span>Evidence Sync</span>
                    <strong>Live</strong>
                    <small>Latest scan 14 minutes ago</small>
                  </article>
                </div>
                <div className="mock-panels">
                  <div className="mock-panel">
                    <div className="panel-title-row">
                      <span className="mini-label">Priority Queue</span>
                      <span className="pill pill-warning">3 open</span>
                    </div>
                    <ul className="signal-list">
                      <li>
                        <span>Vendor review exceptions</span>
                        <strong>2 pending</strong>
                      </li>
                      <li>
                        <span>Policy approvals</span>
                        <strong>6 queued</strong>
                      </li>
                      <li>
                        <span>Risk committee review</span>
                        <strong>Today</strong>
                      </li>
                    </ul>
                  </div>
                  <div className="mock-panel">
                    <div className="panel-title-row">
                      <span className="mini-label">Governance Coverage</span>
                      <span className="pill pill-success">Stable</span>
                    </div>
                    <div className="coverage-bars">
                      <div>
                        <label>DPDP controls</label>
                        <div className="bar">
                          <span style={{ width: "94%" }} />
                        </div>
                      </div>
                      <div>
                        <label>AI governance</label>
                        <div className="bar">
                          <span style={{ width: "88%" }} />
                        </div>
                      </div>
                      <div>
                        <label>Vendor compliance</label>
                        <div className="bar">
                          <span style={{ width: "81%" }} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="trust-section">
        <div className="container">
          <div className="section-heading centered">
            <p className="section-kicker">Built for Compliance Teams</p>
            <h2>Structured for the operators who need readiness, not just reports.</h2>
          </div>
          <div className="badge-row">
            {platformHighlights.map((item) => (
              <div key={item} className="trust-badge">
                <span>✓</span>
                <strong>{item}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section" id="platform">
        <div className="container">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Platform</p>
              <h2>One operating layer for compliance, governance, evidence, and execution.</h2>
            </div>
            <div className="section-cta">
              <a className="button button-secondary" href={appUrl} target="_blank" rel="noreferrer">
                Launch App
              </a>
            </div>
          </div>
          <div className="platform-overview">
            <article className="surface-card narrative-card">
              <p>
                CompliSense-AI is designed for teams that need a software system for compliance operations, not another
                static document library. Track what exists, what is missing, who owns it, and what must happen next.
              </p>
              <div className="narrative-grid">
                <div>
                  <span className="mini-label">Operational focus</span>
                  <strong>Continuous readiness</strong>
                </div>
                <div>
                  <span className="mini-label">Workflow model</span>
                  <strong>Policies, risks, vendors, evidence</strong>
                </div>
                <div>
                  <span className="mini-label">Access point</span>
                  <strong>Live SaaS plus local workflows</strong>
                </div>
              </div>
            </article>
            <article className="surface-card link-card">
              <span className="mini-label">Live product entry points</span>
              <ul>
                <li>
                  <a href={appUrl} target="_blank" rel="noreferrer">
                    Launch product dashboard
                  </a>
                </li>
                <li>
                  <a href={`${appUrl}/reports`} target="_blank" rel="noreferrer">
                    Review reports workspace
                  </a>
                </li>
                <li>
                  <a href={`${appUrl}/about`} target="_blank" rel="noreferrer">
                    View product information page
                  </a>
                </li>
                <li>
                  <a href={`${apiUrl}/health`} target="_blank" rel="noreferrer">
                    Check API health endpoint
                  </a>
                </li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      <section className="content-section" id="solutions">
        <div className="container">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Solutions</p>
              <h2>Core workflows for modern compliance teams.</h2>
            </div>
            <div className="section-cta">
              <a className="button button-secondary" href="#contact-section">
                Talk to Us
              </a>
            </div>
          </div>
          <div className="feature-grid">
            {featureCards.map((feature) => (
              <article key={feature.title} className="surface-card feature-card">
                <div className="feature-icon">
                  <Icon kind={feature.icon} />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="container two-column">
          <div className="section-heading compact">
            <div>
              <p className="section-kicker">How It Works</p>
              <h2>From fragmented compliance to a live operating system.</h2>
            </div>
            <p className="section-copy">
              Move from disconnected files and reactive reviews to a process that can be repeated, monitored, and
              defended.
            </p>
          </div>
          <div className="workflow-stack">
            {workflowSteps.map((item) => (
              <article key={item.step} className="surface-card workflow-card">
                <span className="workflow-step">{item.step}</span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section" id="pricing">
        <div className="container">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Impact</p>
              <h2>Operational gains that matter when teams are small and expectations are high.</h2>
            </div>
            <div className="section-cta">
              <a className="button button-secondary" href={demoMailto}>
                Book Demo
              </a>
            </div>
          </div>
          <div className="metrics-grid">
            {metrics.map((metric) => (
              <article key={metric.label} className="surface-card stats-card">
                <strong>{metric.value}</strong>
                <span>{metric.label}</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="container security-layout">
          <div className="section-heading compact">
            <div>
              <p className="section-kicker">Security & Governance</p>
              <h2>Enterprise-Grade Security & Governance</h2>
            </div>
            <p className="section-copy">
              The platform is positioned for organizations that need traceable operations, clear permissions, and
              evidence-backed governance workflows.
            </p>
          </div>
          <div className="security-grid">
            {securityItems.map((item) => (
              <div key={item} className="security-item">
                <span className="security-dot" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section testimonials-section">
        <div className="container">
          <div className="section-heading centered">
            <p className="section-kicker">What Leaders Say</p>
            <h2>Built to look credible in front of founders, operators, and buyers.</h2>
          </div>
        </div>
        <div className="testimonial-marquee">
          <div className="testimonial-track">
            {[...testimonials, ...testimonials, ...testimonials].map((item, index) => (
              <article key={`${item.author}-${index}`} className="surface-card testimonial-card">
                <p>{item.quote}</p>
                <strong>{item.author}</strong>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section faq-section">
        <div className="container">
          <div className="section-heading">
            <div>
              <p className="section-kicker">FAQ</p>
              <h2>Clear answers for teams evaluating a compliance platform.</h2>
            </div>
            <div className="section-cta">
              <a className="button button-secondary" href="/about">
                Learn More
              </a>
            </div>
          </div>
          <div className="faq-list">
            {faqItems.map((item) => (
              <details key={item.question} className="surface-card faq-item">
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section" id="contact-section">
        <div className="container contact-band">
          <div className="contact-copy">
            <p className="section-kicker">Contact</p>
            <h2>Ready to centralize compliance operations?</h2>
            <p className="section-copy">
              Book a demo to see how CompliSense-AI supports DPDP readiness, AI governance, vendor reviews, policy
              operations, and audit preparation in one system.
            </p>
            <div className="contact-links">
              <a href={`mailto:${supportEmail}`}>{supportEmail}</a>
              <a href={appUrl} target="_blank" rel="noreferrer">
                Launch App
              </a>
            </div>
          </div>
          <div className="surface-card contact-panel">
            <div className="contact-field-grid">
              <div className="field">
                <label>Name</label>
                <div className="field-shell">Founder / Compliance Lead</div>
              </div>
              <div className="field">
                <label>Email</label>
                <div className="field-shell">you@company.com</div>
              </div>
              <div className="field">
                <label>Company</label>
                <div className="field-shell">Your organization</div>
              </div>
              <div className="field field-full">
                <label>Message</label>
                <div className="field-shell field-shell-tall">
                  We are evaluating a compliance platform for DPDP, AI governance, vendor reviews, and audit readiness.
                </div>
              </div>
            </div>
            <div className="contact-actions">
              <Link className="button button-primary" href="/contact">
                Book Demo
              </Link>
              <a className="button button-secondary" href={demoMailto}>
                Email Support
              </a>
            </div>
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container footer-grid">
          <div className="footer-brand">
            <img src="/logo.svg" alt="CompliSense-AI" className="footer-logo" />
            <p>AI-native compliance platform for DPDP, AI governance, policy management, vendor reviews, and audit readiness.</p>
          </div>
          <div className="footer-links">
            <Link href="/#platform">Platform</Link>
            <Link href="/#pricing">Pricing</Link>
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/terms">Terms of Service</Link>
            <Link href="/contact">Contact</Link>
          </div>
          <div className="footer-meta">
            <a href={appUrl} target="_blank" rel="noreferrer">Launch App</a>
            <a href={`mailto:${supportEmail}`}>{supportEmail}</a>
            <span>© 2026 CompliSense-AI</span>
            <span>All rights reserved.</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
