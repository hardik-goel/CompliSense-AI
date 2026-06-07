"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { 
  ShieldCheck, 
  Cpu, 
  BarChart3, 
  FileText, 
  ClipboardList, 
  Building2, 
  ArrowRight,
  Download,
  Check,
  X,
  Star,
  Users,
  Terminal,
  Server,
  Code2,
  Package
} from "lucide-react";

// Inline Social Icons
const LinkedInIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>
  </svg>
);

const GitHubIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>
  </svg>
);

const appUrl = "https://app.complisenseai.com";
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.complisenseai.com";
const supportEmail = "support@complisenseai.com";
const demoMailto = `mailto:${supportEmail}?subject=Book%20a%20Demo%20with%20CompliSense-AI`;

export default function HomePage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.setAttribute("data-visible", "true");
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll("[data-animate]").forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <main className="site-shell">
      {/* NAVIGATION */}
      <header className={`site-header ${isScrolled ? "scrolled" : ""}`}>
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" />
          </Link>
          <nav className="site-nav">
            <a href="#platform">Platform</a>
            <a href="#solutions">Solutions</a>
            <a href="#pricing">Pricing</a>
            <a href="#about">About</a>
          </nav>
          <div className="header-actions">
            <a href="#contact" className="btn-ghost">Contact</a>
            <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">Launch App &rarr;</a>
            <button className="mobile-menu-btn" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* MOBILE MENU */}
      <div className={`mobile-nav-overlay ${mobileMenuOpen ? "open" : ""}`}>
        <a href="#platform" onClick={() => setMobileMenuOpen(false)}>Platform</a>
        <a href="#solutions" onClick={() => setMobileMenuOpen(false)}>Solutions</a>
        <a href="#pricing" onClick={() => setMobileMenuOpen(false)}>Pricing</a>
        <a href="#about" onClick={() => setMobileMenuOpen(false)}>About</a>
        <a href="#contact" onClick={() => setMobileMenuOpen(false)}>Contact</a>
        <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ width: "fit-content" }}>Launch App &rarr;</a>
      </div>

      {/* HERO SECTION */}
      <section className="hero-section">
        <div className="hero-glow"></div>
        <div className="container hero-content">
          <div className="hero-copy">
            <div className="hero-eyebrow" data-animate>
              <Star size={14} fill="currentColor" />
              <span>Now supporting DPDP India Extended v1</span>
            </div>
            <h1 className="hero-headline" data-animate>
              Compliance that <span className="highlight">runs</span> itself.
            </h1>
            <p className="hero-subtext body-text" data-animate>
              DPDP, AI governance, vendor reviews, and audit readiness — automated from one operating layer.
            </p>
            <div className="hero-actions" data-animate>
              <a href={demoMailto} className="btn-primary">Book a Demo <ArrowRight size={16} style={{ marginLeft: "8px" }} /></a>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-ghost">Launch App</a>
            </div>
            <div className="social-proof-bar" data-animate>
              <p className="social-proof-text">Trusted by founders and compliance leads across India</p>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", color: "var(--warning)", fontSize: "14px", marginTop: "-48px", marginBottom: "64px" }}>
                <Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" />
                <span style={{ color: "var(--text-secondary)", marginLeft: "4px" }}>"Within weeks we had a centralised workspace..." — Founder, Multi-City Media Platform</span>
              </div>
            </div>
          </div>

          <div className="dashboard-card" data-animate>
            <div className="stat-item">
              <span className="label-caption">Compliance Score</span>
              <div className="stat-value"><div className="stat-dot green"></div>94%</div>
            </div>
            <div className="stat-item">
              <span className="label-caption">Policies Managed</span>
              <div className="stat-value"><div className="stat-dot blue"></div>128</div>
            </div>
            <div className="stat-item">
              <span className="label-caption">Vendor Assessments</span>
              <div className="stat-value"><div className="stat-dot blue"></div>42</div>
            </div>
            <div className="stat-item">
              <span className="label-caption">DPDP Readiness</span>
              <div className="stat-value"><div className="stat-dot green"></div>Ready</div>
            </div>
            
            <div className="dashboard-card-mini">
              <div className="scan-row">
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div className="stat-dot green"></div> DPDP Core Scan
                </span>
                <span>June 5, 2026</span>
              </div>
              <div className="scan-row">
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div className="stat-dot green"></div> EU AI Act Extended
                </span>
                <span>June 4, 2026</span>
              </div>
              <div className="scan-row">
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div className="stat-dot amber" style={{ background: "var(--warning)" }}></div> Risk Register Update
                </span>
                <span>June 1, 2026</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* LOGO / SOCIAL PROOF BAR */}
      <section className="logo-bar">
        <div className="container logo-bar-inner">
          <span className="logo-bar-text">Trusted by teams at &rarr;</span>
          <div className="logo-placeholder"></div>
          <div className="logo-placeholder"></div>
          <div className="logo-placeholder"></div>
          <div className="logo-placeholder"></div>
        </div>
      </section>

      {/* FRAMEWORK BADGES */}
      <div className="container">
        <div className="framework-strip" data-animate>
          <span className="label-caption" style={{ marginRight: "12px" }}>Supported Frameworks:</span>
          <div className="framework-badge">EU AI Act</div>
          <div className="framework-badge">DPDP India Core</div>
          <div className="framework-badge">DPDP India Extended</div>
          <div className="framework-badge">ISO 42001 Ready</div>
          <div className="framework-badge">More coming</div>
        </div>
      </div>

      {/* FEATURES / PLATFORM SECTION */}
      <section className="content-section" id="platform">
        <div className="container">
          <div className="section-header" data-animate>
            <p className="label-caption">PLATFORM</p>
            <h2 style={{ margin: "12px 0 16px" }}>One system for every compliance workflow.</h2>
            <p className="body-text" style={{ maxWidth: "560px" }}>
              From policy management to vendor reviews — tracked, automated, and audit-ready.
            </p>
          </div>
          
          <div className="feature-grid">
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><ShieldCheck size={20} /></div>
              <h3 className="card-title">DPDP Compliance</h3>
              <p className="body-text">Map obligations to workflows. Maintain evidence. Stay ready.</p>
              <div className="replaces-callout">Replaces: legal spreadsheets and consultant-led reviews</div>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><Cpu size={20} /></div>
              <h3 className="card-title">AI Governance</h3>
              <p className="body-text">Document models, accountability, and controls across teams.</p>
              <div className="replaces-callout">Replaces: ad-hoc model registers and email approvals</div>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><BarChart3 size={20} /></div>
              <h3 className="card-title">Risk Assessments</h3>
              <p className="body-text">Track open risks, owners, and remediation cycles in real time.</p>
              <div className="replaces-callout">Replaces: manual trackers with no owner accountability</div>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><FileText size={20} /></div>
              <h3 className="card-title">Policy Management</h3>
              <p className="body-text">Versioned policies tied to real operational controls.</p>
              <div className="replaces-callout">Replaces: shared drives with unversioned Word docs</div>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><ClipboardList size={20} /></div>
              <h3 className="card-title">Audit Trails</h3>
              <p className="body-text">Durable record of scans, changes, approvals, and evidence.</p>
              <div className="replaces-callout">Replaces: reconstructing evidence from emails the night before</div>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><Building2 size={20} /></div>
              <h3 className="card-title">Vendor Compliance</h3>
              <p className="body-text">Structured reviews with risk signals, not email threads.</p>
              <div className="replaces-callout">Replaces: questionnaire email threads with no tracking</div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS SECTION */}
      <section className="content-section" id="solutions">
        <div className="container">
          <div className="section-header" data-animate>
            <p className="label-caption">HOW IT WORKS</p>
            <h2 style={{ margin: "12px 0" }}>Operational in weeks, not months.</h2>
          </div>
          
          <div className="steps-row">
            <div className="steps-line"></div>
            <div className="step-item" data-animate>
              <div className="step-circle">01</div>
              <h3 className="card-title">Connect</h3>
              <p className="body-text">Import policies, controls, vendors, and documents into one structured workspace.</p>
            </div>
            <div className="step-item" data-animate>
              <div className="step-circle">02</div>
              <h3 className="card-title">Automate</h3>
              <p className="body-text">Generate workflows, evidence collection, and governance operations around your programme.</p>
            </div>
            <div className="step-item" data-animate>
              <div className="step-circle">03</div>
              <h3 className="card-title">Stay Ready</h3>
              <p className="body-text">Continuous monitoring, traceable decisions, and an always-current audit trail.</p>
            </div>
            <div className="step-item" data-animate>
              <div className="step-circle">04</div>
              <h3 className="card-title">Download & Defend</h3>
              <p className="body-text">Export audit-ready packages: findings PDF, evidence ZIP, and decision log — ready for regulators or investors.</p>
            </div>
          </div>

          <div className="section-header" style={{ marginTop: "96px" }} data-animate>
            <h2>Built for engineers. Trusted by compliance leads.</h2>
          </div>
          <div className="arch-grid">
            <div className="arch-card" data-animate>
              <span className="arch-label">Local Agent</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Evidence stays local</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>The collection agent runs on your machine. No raw data ever leaves your environment.</p>
            </div>
            <div className="arch-card" data-animate>
              <span className="arch-label">SaaS Dashboard</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Centralised insights</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Scan metadata, findings, and audit trails sync to a hosted dashboard. Inspect anywhere.</p>
            </div>
            <div className="arch-card" data-animate>
              <span className="arch-label">API-First</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Programmable flows</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Every action is API-accessible. Integrate with CI/CD, Slack, or JIRA seamlessly.</p>
            </div>
            <div className="arch-card" data-animate>
              <span className="arch-label">Rulepack Model</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Market Agnostic</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Compliance logic is versioned rulepacks. Switch markets without changing code.</p>
            </div>
          </div>
        </div>
      </section>

      {/* METRICS / IMPACT SECTION */}
      <section className="metrics-band" id="pricing">
        <div className="container">
          <div className="metrics-grid">
            <div className="metric-item" data-animate>
              <strong>&lt; 8 weeks</strong>
              <span>To first audit readiness</span>
            </div>
            <div className="metric-item" data-animate>
              <strong>60%</strong>
              <span>Reduction in compliance work</span>
            </div>
            <div className="metric-item" data-animate>
              <strong>100%</strong>
              <span>Evidence stays on your machine</span>
            </div>
            <div className="metric-item" data-animate>
              <strong>4</strong>
              <span>Frameworks supported today</span>
            </div>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS SECTION */}
      <section className="content-section">
        <div className="container">
          <div className="section-header" data-animate>
            <p className="label-caption">WHAT TEAMS SAY</p>
            <h2 style={{ margin: "12px 0" }}>Built for operators who need readiness, not reports.</h2>
          </div>
          
          <div className="testimonials-grid">
            <div className="testimonial-card" data-animate>
              <div className="stars">
                <Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" />
              </div>
              <p className="testimonial-quote">"Within weeks we had a centralised workspace, automated workflows, and significantly faster audit readiness."</p>
              <div className="testimonial-author-wrap">
                <div className="author-avatar">F</div>
                <div className="author-info">
                  <span className="author-name">Founder</span>
                  <span className="author-title">Multi-City Media Platform</span>
                </div>
              </div>
            </div>
            <div className="testimonial-card" data-animate>
              <div className="stars">
                <Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" />
              </div>
              <p className="testimonial-quote">"CompliSense-AI helped us standardise governance workflows, centralise evidence, and stay audit-ready without adding overhead."</p>
              <div className="testimonial-author-wrap">
                <div className="author-avatar">C</div>
                <div className="author-info">
                  <span className="author-name">CEO & Founder</span>
                  <span className="author-title">Data Intelligence Company</span>
                </div>
              </div>
            </div>
            <div className="testimonial-card" data-animate>
              <div className="stars">
                <Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" />
              </div>
              <p className="testimonial-quote">"The DPDP readiness module alone saved us three weeks of legal prep. The audit trail export is exactly what our DPO needed."</p>
              <div className="testimonial-author-wrap">
                <div className="author-avatar">H</div>
                <div className="author-info">
                  <span className="author-name">Head of Data Operations</span>
                  <span className="author-title">Series A Fintech</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* COMPARISON SECTION */}
      <section className="content-section">
        <div className="container">
          <div className="section-header" style={{ textAlign: "center" }} data-animate>
            <h2>You already have spreadsheets.<br/>Here's what you're missing.</h2>
          </div>
          
          <div className="comparison-wrap" data-animate>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>What you need</th>
                  <th>Spreadsheets + Email</th>
                  <th className="check-col">CompliSense-AI</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Evidence collection</td>
                  <td className="cross-col"><X size={16} /> Manual, error-prone</td>
                  <td className="check-col"><Check size={16} className="status-check" /> Automated local agent</td>
                </tr>
                <tr>
                  <td>Version control</td>
                  <td className="cross-col"><X size={16} /> Shared drives, conflicts</td>
                  <td className="check-col"><Check size={16} className="status-check" /> Versioned policy records</td>
                </tr>
                <tr>
                  <td>Audit trail</td>
                  <td className="cross-col"><X size={16} /> Reconstruct from emails</td>
                  <td className="check-col"><Check size={16} className="status-check" /> Durable, immutable log</td>
                </tr>
                <tr>
                  <td>Vendor reviews</td>
                  <td className="cross-col"><X size={16} /> Email threads, no tracking</td>
                  <td className="check-col"><Check size={16} className="status-check" /> Structured, scored reviews</td>
                </tr>
                <tr>
                  <td>DPDP readiness</td>
                  <td className="cross-col"><X size={16} /> Consultant + guesswork</td>
                  <td className="check-col"><Check size={16} className="status-check" /> Built-in rulepack, always current</td>
                </tr>
                <tr>
                  <td>Time to audit-ready</td>
                  <td className="cross-col">3–6 months</td>
                  <td className="check-col" style={{ fontWeight: "700" }}>&lt; 8 weeks</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* SECURITY TRUST SECTION */}
      <section className="content-section">
        <div className="container">
          <div className="section-header" data-animate>
            <p className="label-caption">SECURITY & PRIVACY</p>
            <h2 style={{ margin: "12px 0" }}>Your data never leaves your machine.</h2>
          </div>
          
          <div className="security-grid">
            <div className="security-item" data-animate>
              <div className="icon-box"><ShieldCheck size={24} /></div>
              <strong className="author-name">Local evidence collection</strong>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>The scanning agent runs locally. Raw artefacts stay on your machine.</p>
            </div>
            <div className="security-item" data-animate>
              <div className="icon-box"><Package size={24} /></div>
              <strong className="author-name">Metadata only</strong>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Only scan findings and metadata sync to the dashboard. Never raw documents.</p>
            </div>
            <div className="security-item" data-animate>
              <div className="icon-box"><Check size={24} /></div>
              <strong className="author-name">JWT + API key auth</strong>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Every API call is authenticated. No anonymous access allowed.</p>
            </div>
            <div className="security-item" data-animate>
              <div className="icon-box"><Building2 size={24} /></div>
              <strong className="author-name">India-hosted roadmap</strong>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Data residency options planned for 2026 to ensure compliance.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ SECTION */}
      <section className="content-section">
        <div className="container">
          <div className="section-header" style={{ textAlign: "center" }} data-animate>
            <h2>Common questions.</h2>
          </div>
          
          <div className="faq-list">
            <details className="faq-item" data-animate>
              <summary>What does CompliSense-AI replace?</summary>
              <p>It replaces fragmented compliance operations spread across spreadsheets, shared drives, email threads, and consulting-heavy manual processes.</p>
            </details>
            <details className="faq-item" data-animate>
              <summary>Who is this built for?</summary>
              <p>The platform is designed for startups, SMBs, and mid-market teams that need an operational compliance system without building an internal platform from scratch.</p>
            </details>
            <details className="faq-item" data-animate>
              <summary>Is this a SaaS dashboard or do I need to install something?</summary>
              <p>Both. The dashboard is fully cloud-hosted at app.complisenseai.com. The local agent (optional) runs on your machine to collect evidence from your file system — raw data never leaves your environment.</p>
            </details>
            <details className="faq-item" data-animate>
              <summary>How is CompliSense-AI different from a compliance consultant?</summary>
              <p>Consultants leave when the retainer ends. CompliSense-AI is an operational system — it runs continuously, tracks changes, maintains evidence, and keeps your programme current between audits.</p>
            </details>
            <details className="faq-item" data-animate>
              <summary>Which regulations do you support today?</summary>
              <p>DPDP India (core and extended), EU AI Act (core and extended). ISO 42001 alignment is on the roadmap. Adding a new market takes a new rulepack, not a product rebuild.</p>
            </details>
            <details className="faq-item" data-animate>
              <summary>How does the platform connect to the live product?</summary>
              <p>The marketing site lives at complisenseai.com. The customer application is accessible via the Launch App button above, and API traffic is isolated for security.</p>
            </details>
          </div>
        </div>
      </section>

      {/* ABOUT SECTION */}
      <section className="content-section" id="about">
        <div className="container">
          <div className="section-header" data-animate>
            <p className="label-caption">ABOUT US</p>
            <h2 style={{ margin: "12px 0" }}>Built by practitioners, for operators.</h2>
            <p className="body-text" style={{ maxWidth: "680px", marginTop: "24px" }}>
              CompliSense-AI was founded by engineers who lived the compliance chaos firsthand — fragmented spreadsheets, audit panic, and consultants who left when the retainer ended. We built the system we wished existed.
            </p>
          </div>

          <div className="feature-grid">
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><ShieldCheck size={20} /></div>
              <h3 className="card-title">India-First</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Built natively for DPDP, not retrofitted from EU frameworks.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><Terminal size={20} /></div>
              <h3 className="card-title">Operator-Grade</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Evidence collection, workflow automation, and audit trails — not just dashboards.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><Users size={20} /></div>
              <h3 className="card-title">No Lock-In</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Your data, your exports, your control. Always.</p>
            </div>
          </div>

          <div style={{ textAlign: "center", marginTop: "64px" }} data-animate>
            <p className="body-text">Want to know more? <a href="#contact" style={{ color: "var(--accent)", fontWeight: "600" }}>Book a 30-minute call &rarr;</a></p>
          </div>
        </div>
      </section>

      {/* CTA / CONTACT SECTION */}
      <section className="content-section" id="contact" style={{ paddingBottom: 0 }}>
        <div className="container">
          <div className="cta-section" data-animate>
            <h2>Ready to centralise your compliance operations?</h2>
            <p>Book a 30-minute demo. See the platform live.</p>
            <div className="cta-actions">
              <a href={demoMailto} className="btn-primary">Book a Demo <ArrowRight size={16} style={{ marginLeft: "8px" }} /></a>
              <a href="https://www.linkedin.com/company/complisense-ai" target="_blank" rel="noopener noreferrer" className="btn-ghost">
                <LinkedInIcon size={16} /> <span style={{ marginLeft: "8px" }}>Connect on LinkedIn</span>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="site-footer">
        <div className="container">
          <div className="footer-top">
            <div className="footer-brand">
              <img src="/logo.png" alt="CompliSense-AI" style={{ height: "40px", marginBottom: "16px" }} />
              <p>AI-native compliance for modern teams.</p>
              <div className="social-links">
                <a href="https://www.linkedin.com/company/complisense-ai" target="_blank" rel="noopener noreferrer" className="social-link">
                  <LinkedInIcon size={20} />
                </a>
                <a href="https://github.com/hardik-goel/CompliSense-AI" target="_blank" rel="noopener noreferrer" className="social-link">
                  <GitHubIcon size={20} />
                </a>
              </div>
            </div>
            <div className="footer-col">
              <strong>Product</strong>
              <a href="#platform">Platform</a>
              <a href="#solutions">Solutions</a>
              <a href="#pricing">Pricing</a>
              <a href={appUrl} target="_blank" rel="noopener noreferrer">Launch App</a>
            </div>
            <div className="footer-col">
              <strong>Compliance</strong>
              <a href="#platform">DPDP India</a>
              <a href="#platform">EU AI Act</a>
              <a href="#platform">ISO 42001</a>
            </div>
            <div className="footer-col">
              <strong>Company</strong>
              <a href="#about">About</a>
              <a href="#contact">Contact</a>
              <Link href="/privacy">Privacy Policy</Link>
              <Link href="/terms">Terms</Link>
            </div>
          </div>
          <div className="footer-bottom">
            <span>&copy; 2026 CompliSense-AI &middot; Built in India 🇮🇳</span>
            <a href={`mailto:${supportEmail}`} style={{ color: "var(--text-muted)", textDecoration: "underline" }}>{supportEmail}</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
