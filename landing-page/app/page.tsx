"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://complisense-ai-backend.onrender.com";
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.complisenseai.com";
const supportEmail = "support@complisenseai.com";
const demoMailto = `mailto:${supportEmail}?subject=Book%20a%20Demo%20with%20CompliSense-AI`;

function ShieldCheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

function CpuChipIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
      <rect x="9" y="9" width="6" height="6" />
      <line x1="9" y1="1" x2="9" y2="4" />
      <line x1="15" y1="1" x2="15" y2="4" />
      <line x1="9" y1="20" x2="9" y2="23" />
      <line x1="15" y1="20" x2="15" y2="23" />
      <line x1="20" y1="9" x2="23" y2="9" />
      <line x1="20" y1="14" x2="23" y2="14" />
      <line x1="1" y1="9" x2="4" y2="9" />
      <line x1="1" y1="14" x2="4" y2="14" />
    </svg>
  );
}

function ChartBarIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function DocumentTextIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function ClipboardListIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
      <path d="M12 11h4" />
      <path d="M12 16h4" />
      <path d="M8 11h.01" />
      <path d="M8 16h.01" />
    </svg>
  );
}

function BuildingOfficeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
      <path d="M9 22v-4h6v4" />
      <path d="M8 6h.01" />
      <path d="M16 6h.01" />
      <path d="M12 6h.01" />
      <path d="M12 10h.01" />
      <path d="M12 14h.01" />
      <path d="M16 10h.01" />
      <path d="M16 14h.01" />
      <path d="M8 10h.01" />
      <path d="M8 14h.01" />
    </svg>
  );
}

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
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" style={{ height: "40px" }} />
          </Link>
          <nav className="site-nav">
            <a href="#platform">Platform</a>
            <a href="#solutions">Solutions</a>
            <a href="#pricing">Pricing</a>
            <Link href="/about">About</Link>
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
        <Link href="/about" onClick={() => setMobileMenuOpen(false)}>About</Link>
        <a href="#contact" onClick={() => setMobileMenuOpen(false)}>Contact</a>
        <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ width: "fit-content" }}>Launch App &rarr;</a>
      </div>

      {/* HERO SECTION */}
      <section className="hero-section">
        <div className="hero-glow"></div>
        <div className="container hero-content">
          <div className="hero-copy">
            <p className="label-caption" data-animate>AI-NATIVE COMPLIANCE PLATFORM</p>
            <h1 data-animate style={{ marginTop: "16px" }}>Compliance that runs itself.</h1>
            <p className="hero-subtext body-text" data-animate>
              DPDP, AI governance, vendor reviews, and audit readiness — automated from one operating layer.
            </p>
            <div className="hero-actions" data-animate>
              <a href={demoMailto} className="btn-primary">Book a Demo &rarr;</a>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-ghost">Launch App</a>
            </div>
            <p className="social-proof-text" data-animate>Trusted by founders and compliance leads across India</p>
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
              <div className="icon-wrap"><ShieldCheckIcon /></div>
              <h3 className="card-title">DPDP Compliance</h3>
              <p className="body-text">Map obligations to workflows. Maintain evidence. Stay ready.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><CpuChipIcon /></div>
              <h3 className="card-title">AI Governance</h3>
              <p className="body-text">Document models, accountability, and controls across teams.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><ChartBarIcon /></div>
              <h3 className="card-title">Risk Assessments</h3>
              <p className="body-text">Track open risks, owners, and remediation cycles in real time.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><DocumentTextIcon /></div>
              <h3 className="card-title">Policy Management</h3>
              <p className="body-text">Versioned policies tied to real operational controls.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><ClipboardListIcon /></div>
              <h3 className="card-title">Audit Trails</h3>
              <p className="body-text">Durable record of scans, changes, approvals, and evidence.</p>
            </div>
            <div className="feature-card" data-animate>
              <div className="icon-wrap"><BuildingOfficeIcon /></div>
              <h3 className="card-title">Vendor Compliance</h3>
              <p className="body-text">Structured reviews with risk signals, not email threads.</p>
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
          </div>
        </div>
      </section>

      {/* METRICS / IMPACT SECTION */}
      <section className="metrics-band" id="pricing">
        <div className="container">
          <div className="metrics-grid">
            <div className="metric-item" data-animate>
              <strong>60%</strong>
              <span>Reduction in compliance effort</span>
            </div>
            <div className="metric-item" data-animate>
              <strong>120+</strong>
              <span>Policies and records centralised</span>
            </div>
            <div className="metric-item" data-animate>
              <strong>8 weeks</strong>
              <span>To full operational readiness</span>
            </div>
            <div className="metric-item" data-animate>
              <strong>Hours</strong>
              <span>Instead of days for audit prep</span>
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
              <p className="testimonial-quote">"Within weeks we had a centralised workspace, automated workflows, and significantly faster audit readiness."</p>
              <span className="testimonial-author">Founder, Multi-City Media Platform</span>
            </div>
            <div className="testimonial-card" data-animate>
              <p className="testimonial-quote">"CompliSense-AI helped us standardise governance workflows, centralise evidence, and stay audit-ready without adding operational overhead."</p>
              <span className="testimonial-author">CEO & Founder, Data & Operations Intelligence Company</span>
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
              <summary>How does the platform connect to the live product?</summary>
              <p>The marketing site lives at complisenseai.com, The customer application is accessible via the Launch App button above, and API traffic is isolated at api.complisenseai.com.</p>
            </details>
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
              <a href={demoMailto} className="btn-primary">Book a Demo &rarr;</a>
              <a href={`mailto:${supportEmail}`} className="btn-ghost">{supportEmail}</a>
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
            </div>
            <div className="footer-links-grid">
              <div className="footer-col">
                <strong>Product</strong>
                <a href="#platform">Platform</a>
                <a href="#pricing">Pricing</a>
                <a href={appUrl} target="_blank" rel="noopener noreferrer">Launch App</a>
              </div>
              <div className="footer-col">
                <strong>Company</strong>
                <Link href="/about">About</Link>
                <a href="#contact">Contact</a>
                <Link href="/privacy">Privacy Policy</Link>
                <Link href="/terms">Terms</Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <span>&copy; 2026 CompliSense-AI &middot; All rights reserved.</span>
            <a href={`mailto:${supportEmail}`}>{supportEmail}</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
