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
const calendlyUrl = "https://calendly.com/hardik-goel214/complisense-ai";

export default function HomePage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showBanner, setShowBanner] = useState(true);
  const [activeTab, setActiveTab] = useState("DPDP");
  const [scanState, setScanState] = useState(1); // 1: Scanning, 2: Results

  useEffect(() => {
    const bannerDismissed = sessionStorage.getItem(" CS-Banner-Dismissed");
    if (bannerDismissed) setShowBanner(false);

    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
      const fab = document.getElementById('floating-cta');
      if (fab) {
        if (window.scrollY > 500) {
          fab.classList.add('visible');
        } else {
          fab.classList.remove('visible');
        }
      }
    };
    window.addEventListener("scroll", handleScroll);

    const runCountup = () => {
      document.querySelectorAll('.countup').forEach(el => {
        const target = parseInt((el as HTMLElement).dataset.target || "0");
        let current = 0;
        const step = Math.max(1, Math.floor(target / 30));
        const timer = setInterval(() => {
          current = Math.min(current + step, target);
          el.textContent = current.toString();
          if (current >= target) clearInterval(timer);
        }, 40);
      });
    };

    const countupObserver = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { 
        runCountup(); 
        countupObserver.disconnect(); 
      }
    }, { threshold: 0.5 });
    
    const counterBar = document.querySelector('.countup')?.parentElement?.parentElement?.parentElement;
    if (counterBar) countupObserver.observe(counterBar);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      countupObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setScanState(prev => (prev === 1 ? 2 : 1));
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const dismissBanner = () => {
    setShowBanner(false);
    sessionStorage.setItem("CS-Banner-Dismissed", "true");
  };

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelectorAll('[data-animate], .fade-up').forEach((el) => {
        el.setAttribute("data-visible", "true");
        el.classList.add("visible");
      });
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.setAttribute("data-visible", "true");
          entry.target.classList.add("visible");
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll("[data-animate], .fade-up").forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setMobileMenuOpen(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const nav = document.querySelector('nav');
      const mobileBtn = document.querySelector('.mobile-menu-btn');
      if (nav && !nav.contains(e.target as Node) && mobileBtn && !mobileBtn.contains(e.target as Node)) {
        setMobileMenuOpen(false);
      }
    };
    if (mobileMenuOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [mobileMenuOpen]);

  return (
    <main className="site-shell">
      {/* ANNOUNCEMENT BANNER */}
      {showBanner && (
        <div className="announcement-banner">
          ✦ CompliSense-AI now supports DPDP India Extended · EU AI Act alignment added · 
          <a href="#platform" onClick={() => setShowBanner(false)}>[Read what's new &rarr;]</a>
          <button className="announcement-close" onClick={dismissBanner}>&times;</button>
        </div>
      )}

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
            <button className="mobile-menu-btn" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} aria-label="Toggle navigation menu" aria-expanded={mobileMenuOpen}>
              {!mobileMenuOpen ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <line x1="3" y1="6" x2="21" y2="6"/>
                  <line x1="3" y1="12" x2="21" y2="12"/>
                  <line x1="3" y1="18" x2="21" y2="18"/>
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              )}
            </button>
          </div>
          
          {/* Mobile menu — only shown on small screens when mobileMenuOpen */}
          {mobileMenuOpen && (
            <div
              className="md:hidden"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: '#07111F',
                borderTop: '1px solid #1B3A5C',
                borderBottom: '1px solid #1B3A5C',
                padding: '16px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                zIndex: 999,
              }}
            >
              <a href="#platform" onClick={() => setMobileMenuOpen(false)}
                 style={{padding:'12px 0', color:'#94A3B8', fontSize:'15px', borderBottom:'1px solid #1B3A5C', textDecoration:'none'}}>
                Platform
              </a>
              <a href="#solutions" onClick={() => setMobileMenuOpen(false)}
                 style={{padding:'12px 0', color:'#94A3B8', fontSize:'15px', borderBottom:'1px solid #1B3A5C', textDecoration:'none'}}>
                Solutions
              </a>
              <a href="#pricing" onClick={() => setMobileMenuOpen(false)}
                 style={{padding:'12px 0', color:'#94A3B8', fontSize:'15px', borderBottom:'1px solid #1B3A5C', textDecoration:'none'}}>
                Pricing
              </a>
              <a href="/about" onClick={() => setMobileMenuOpen(false)}
                 style={{padding:'12px 0', color:'#94A3B8', fontSize:'15px', borderBottom:'1px solid #1B3A5C', textDecoration:'none'}}>
                About
              </a>
              <a href="#contact" onClick={() => setMobileMenuOpen(false)}
                 style={{padding:'12px 0', color:'#94A3B8', fontSize:'15px', borderBottom:'1px solid #1B3A5C', textDecoration:'none'}}>
                Contact
              </a>
              <a href="https://app.complisenseai.com"
                 target="_blank" rel="noopener noreferrer"
                 onClick={() => setMobileMenuOpen(false)}
                 style={{
                   marginTop:'8px', padding:'12px 0', textAlign:'center',
                   background:'#3B82F6', color:'#fff', borderRadius:'8px',
                   fontSize:'15px', fontWeight:600, textDecoration:'none'
                 }}>
                Launch App &rarr;
              </a>
            </div>
          )}
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="hero-section" id="hero">
        <div aria-hidden="true" style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none", zIndex: 0 }}>
          <svg preserveAspectRatio="none" viewBox="0 0 1440 560"
               style={{ position: "absolute", bottom: 0, left: 0, width: "100%", height: "70%", opacity: 0.18 }}
               xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="waveGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style={{ stopColor: "#3B82F6", stopOpacity: 1 }}/>
                <stop offset="100%" style={{ stopColor: "#22D3EE", stopOpacity: 1 }}/>
              </linearGradient>
              <linearGradient id="waveGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style={{ stopColor: "#8B5CF6", stopOpacity: 1 }}/>
                <stop offset="100%" style={{ stopColor: "#3B82F6", stopOpacity: 1 }}/>
              </linearGradient>
            </defs>

            <path fill="url(#waveGrad1)">
              <animate attributeName="d"
                dur="12s" repeatCount="indefinite"
                values="
                  M0,320 C240,280 480,360 720,320 C960,280 1200,360 1440,320 L1440,560 L0,560 Z;
                  M0,300 C240,340 480,260 720,300 C960,340 1200,260 1440,300 L1440,560 L0,560 Z;
                  M0,320 C240,280 480,360 720,320 C960,280 1200,360 1440,320 L1440,560 L0,560 Z
                "/>
            </path>

            <path fill="url(#waveGrad2)" opacity="0.5">
              <animate attributeName="d"
                dur="9s" repeatCount="indefinite"
                values="
                  M0,380 C360,340 720,420 1080,380 C1260,360 1380,400 1440,380 L1440,560 L0,560 Z;
                  M0,360 C360,400 720,340 1080,370 C1260,390 1380,350 1440,360 L1440,560 L0,560 Z;
                  M0,380 C360,340 720,420 1080,380 C1260,360 1380,400 1440,380 L1440,560 L0,560 Z
                "/>
            </path>

            <path fill="url(#waveGrad1)" opacity="0.25">
              <animate attributeName="d"
                dur="7s" repeatCount="indefinite"
                values="
                  M0,420 C180,400 360,440 540,420 C720,400 900,440 1080,420 C1260,400 1380,440 1440,420 L1440,560 L0,560 Z;
                  M0,440 C180,420 360,460 540,440 C720,420 900,460 1080,440 C1260,420 1380,460 1440,440 L1440,560 L0,560 Z;
                  M0,420 C180,400 360,440 540,420 C720,400 900,440 1080,420 C1260,400 1380,440 1440,420 L1440,560 L0,560 Z
                "/>
            </path>
          </svg>

          <div style={{ position: "absolute", inset: 0 }}>
            <span style={{ position: "absolute", width: "3px", height: "3px", borderRadius: "50%", background: "#3B82F6", opacity: 0.4, top: "20%", left: "15%", animation: "floatDot 6s ease-in-out infinite" }}></span>
            <span style={{ position: "absolute", width: "2px", height: "2px", borderRadius: "50%", background: "#22D3EE", opacity: 0.3, top: "35%", left: "30%", animation: "floatDot 8s ease-in-out infinite 1s" }}></span>
            <span style={{ position: "absolute", width: "4px", height: "4px", borderRadius: "50%", background: "#8B5CF6", opacity: 0.25, top: "15%", left: "65%", animation: "floatDot 7s ease-in-out infinite 2s" }}></span>
            <span style={{ position: "absolute", width: "2px", height: "2px", borderRadius: "50%", background: "#3B82F6", opacity: 0.35, top: "50%", left: "80%", animation: "floatDot 9s ease-in-out infinite 0.5s" }}></span>
            <span style={{ position: "absolute", width: "3px", height: "3px", borderRadius: "50%", background: "#22D3EE", opacity: 0.3, top: "25%", left: "50%", animation: "floatDot 5s ease-in-out infinite 3s" }}></span>
          </div>
        </div>
        <div className="hero-glow"></div>
        <div className="container hero-content">
          <div className="hero-copy">
            <div className="hero-eyebrow" data-animate>
              <Star size={14} fill="currentColor" />
              <span>Now supporting DPDP India Extended v1</span>
            </div>
            <h1 className="hero-headline" data-animate>
              Compliance Intelligence. Delivered.
            </h1>
            <p className="hero-subtext body-text" data-animate>
              DPDP, AI governance, vendor reviews, and audit readiness — automated from one operating layer.
            </p>
            <div className="hero-actions" data-animate style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "12px", flexWrap: "wrap" }}>
              <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">
                📅 Book a Demo
              </a>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-ghost">
                Launch App &rarr;
              </a>
              <a href={`mailto:${supportEmail}?subject=CompliSense-AI%20Enquiry`} className="btn-ghost" style={{ fontSize: "13px", color: "#64748B", textDecoration: "underline", border: "none", padding: "0" }}>
                or email us
              </a>
            </div>

            {/* VIDEO EMBED */}
            <div data-animate style={{
              margin: '40px auto 0', maxWidth: '800px', width: '100%',
              borderRadius: '16px', overflow: 'hidden',
              border: '1px solid #1B3A5C',
              boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute', top: '16px', left: '16px', zIndex: 2,
                background: 'rgba(7,17,31,0.85)', border: '1px solid #1B3A5C',
                borderRadius: '6px', padding: '4px 12px',
                fontSize: '11px', color: '#94A3B8', letterSpacing: '1px'
              }}>
                ▶&nbsp; PRODUCT DEMO &nbsp;&middot;&nbsp; 2 MIN
              </div>
              <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
                <iframe
                  src="https://www.youtube-nocookie.com/embed/PWvqFBSR6h8?rel=0&modestbranding=1&color=white"
                  title="CompliSense-AI Product Demo"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  loading="lazy"
                  style={{
                    position: 'absolute', top: 0, left: 0,
                    width: '100%', height: '100%', border: 'none'
                  }}
                />
              </div>
            </div>

            <div className="social-proof-bar" data-animate style={{ marginTop: "48px" }}>
              <p className="social-proof-text">Trusted by founders and compliance leads across India</p>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", color: "var(--warning)", fontSize: "14px", marginTop: "-48px", marginBottom: "64px" }}>
                <Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" /><Star size={14} fill="currentColor" />
                <span style={{ color: "var(--text-secondary)", marginLeft: "4px" }}>"Within weeks we had a centralised workspace..." — Founder, Multi-City Media Platform</span>
              </div>
            </div>
          </div>

          <div data-animate>
            {scanState === 1 ? (
              <div className="scan-widget">
                <div className="widget-header">
                  <span style={{ display: "flex", alignItems: "center" }}>
                    <div className="status-dot pulse"></div> ● CompliSense-AI
                  </span>
                  <span style={{ color: "#22D3EE" }}>━━━━━━━━━━ SCANNING</span>
                </div>
                <div className="scan-line visible typewriter">Checking: EU AI Act · Art. 9</div>
                <div className="scan-line visible" style={{ animationDelay: "0.5s" }}>Checking: DPDP Core obligations</div>
                <div className="scan-line visible" style={{ animationDelay: "1s" }}>Checking: Vendor questionnaire gap...</div>
                <div className="progress-container">
                  <div className="progress-bar-wrap">
                    <div className="progress-bar-fill" style={{ width: "67%", animation: "none" }}></div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", color: "#64748B", fontSize: "10px" }}>
                    <span>Scan progress</span>
                    <span>67%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="scan-widget">
                <div className="widget-header">
                  <span style={{ display: "flex", alignItems: "center" }}>
                    <div className="status-dot fixed"></div> ✓ CompliSense-AI
                  </span>
                  <span style={{ color: "#22C55E" }}>━━━━━━━━━━ COMPLETE</span>
                </div>
                <div className="scan-line visible">
                  <span>✓ Art. 9 — Transparency docs</span>
                  <span className="badge-pass">PASS</span>
                </div>
                <div className="scan-line visible">
                  <span>⚠ DPDP Core — DPO assignment</span>
                  <span className="badge-partial">PARTIAL</span>
                </div>
                <div className="scan-line visible">
                  <span>✗ Vendor questionnaire — 3 gaps</span>
                  <span className="badge-action">ACTION</span>
                </div>
                <div className="progress-container">
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span>Overall Readiness</span>
                    <span>78%</span>
                  </div>
                  <div className="progress-bar-wrap">
                    <div className="progress-bar-fill" style={{ width: "78%" }}></div>
                  </div>
                  <div style={{ color: "#64748B", fontSize: "10px" }}>Next scan: automated · 7 days</div>
                </div>
              </div>
            )}
            <p style={{ fontSize: "11px", color: "#64748B", textAlign: "center", marginTop: "8px" }}>
              * Simulated scan output. Your actual results appear after first scan.
            </p>
          </div>
        </div>
      </section>

      {/* LOGO / SOCIAL PROOF BAR */}
      <section className="logo-bar">
        <div className="container" style={{ textAlign: "center" }}>
          <div className="logo-bar-inner">
            <span className="logo-bar-text">Trusted by teams at &rarr;</span>
            <div className="trust-chip">Media Platform</div>
            <div className="trust-chip">Fintech Startup</div>
            <div className="trust-chip">D&O Intelligence Co.</div>
            <div className="trust-chip">AI SaaS Startup</div>
          </div>
          <p style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "12px" }}>
            Names withheld under NDA. Reference calls available on request.
          </p>
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
          <div className="framework-badge" style={{ borderStyle: "dashed", color: "var(--text-muted)", fontStyle: "italic" }}>+ Expanding Quarterly</div>
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

          {/* TAB SWITCHER */}
          <div className="tab-switcher" data-animate style={{ marginTop: "48px" }}>
            {["DPDP", "AI Governance", "Risk", "Audit", "Vendors"].map(tab => (
              <button 
                key={tab} 
                className={`tab-btn ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="tab-panel fade-up" data-animate>
            <div className="tab-content-left">
              <ul className="bullet-list">
                {activeTab === "DPDP" && (
                  <>
                    <li><ShieldCheck size={18} /> Map obligations to specific business workflows.</li>
                    <li><ShieldCheck size={18} /> Automated evidence collection for DPO reviews.</li>
                    <li><ShieldCheck size={18} /> Real-time readiness score for DPDP sections.</li>
                  </>
                )}
                {activeTab === "AI Governance" && (
                  <>
                    <li><Cpu size={18} /> Register and document AI models across teams.</li>
                    <li><Cpu size={18} /> Apply technical controls based on EU AI Act articles.</li>
                    <li><Cpu size={18} /> Centralised accountability log for model decisions.</li>
                  </>
                )}
                {activeTab === "Risk" && (
                  <>
                    <li><BarChart3 size={18} /> Continuous risk monitoring and scoring.</li>
                    <li><BarChart3 size={18} /> Assign risk owners and track remediation cycles.</li>
                    <li><BarChart3 size={18} /> Historical trends for audit committee reporting.</li>
                  </>
                )}
                {activeTab === "Audit" && (
                  <>
                    <li><ClipboardList size={18} /> Immutable log of all scans and approvals.</li>
                    <li><ClipboardList size={18} /> Export audit-ready PDF findings in seconds.</li>
                    <li><ClipboardList size={18} /> Trace decisions back to raw evidence artefacts.</li>
                  </>
                )}
                {activeTab === "Vendors" && (
                  <>
                    <li><Building2 size={18} /> Structured vendor assessment questionnaires.</li>
                    <li><Building2 size={18} /> Automated risk signalling from vendor responses.</li>
                    <li><Building2 size={18} /> Maintain a live register of third-party processors.</li>
                  </>
                )}
              </ul>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ marginTop: "32px" }}>Try {activeTab} Module &rarr;</a>
            </div>
            <div className="tab-content-right" style={{ display: "flex", justifyContent: "center" }}>
              {activeTab === "DPDP" && (
                <div className="card-visual" style={{ background: "transparent", height: "120px" }}>
                  <div style={{ position: "relative", width: "200px" }}>
                    <div className="pipeline-node" style={{ position: "absolute", left: "0" }}>Map</div>
                    <div className="pipeline-node" style={{ position: "absolute", left: "70px" }}>Scan</div>
                    <div className="pipeline-node" style={{ position: "absolute", left: "140px" }}>Done</div>
                    <div style={{ position: "absolute", top: "12px", left: "30px", width: "120px", height: "1px", background: "var(--border)" }}></div>
                    <div className="pipeline-dot"></div>
                  </div>
                </div>
              )}
              {activeTab === "AI Governance" && (
                <div className="card-visual" style={{ background: "transparent", height: "120px" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div className="stack-layer" style={{ width: "100px" }}>Model</div>
                    <div className="stack-layer middle" style={{ width: "120px" }}>Controls</div>
                    <div className="stack-layer" style={{ width: "100px" }}>Docs</div>
                  </div>
                </div>
              )}
              {activeTab === "Risk" && (
                <div className="card-visual" style={{ background: "transparent", height: "120px", alignItems: "flex-end" }}>
                  <div className="risk-bar" style={{ height: "40%", background: "#EF4444" }}></div>
                  <div className="risk-bar" style={{ height: "60%", background: "#F59E0B" }}></div>
                  <div className="risk-bar" style={{ height: "90%", background: "#10B981" }}></div>
                  <div className="risk-bar" style={{ height: "75%", background: "#3B82F6" }}></div>
                </div>
              )}
              {activeTab === "Audit" && (
                <div className="card-visual" style={{ background: "transparent", height: "120px" }}>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <div className="timeline-dot" style={{ opacity: 1, marginBottom: "8px" }}></div>
                    <div className="timeline-dot" style={{ opacity: 1, marginBottom: "8px", animation: "move-dot 2s infinite", animationDelay: "0.5s" }}></div>
                    <div className="timeline-dot" style={{ opacity: 1, animation: "move-dot 2s infinite", animationDelay: "1s" }}></div>
                  </div>
                </div>
              )}
              {activeTab === "Vendors" && (
                <div className="card-visual" style={{ background: "transparent", height: "120px" }}>
                  <svg width="100" height="100" viewBox="0 0 100 100">
                    <polygon points="50,5 90,25 90,75 50,95 10,75 10,25" fill="none" stroke="var(--border)" strokeWidth="1" />
                    <polygon points="50,30 70,40 70,60 50,70 30,60 30,40" fill="var(--accent)" fillOpacity="0.3" stroke="var(--accent)" strokeWidth="2">
                      <animate attributeName="points" dur="3s" repeatCount="indefinite" values="50,30 70,40 70,60 50,70 30,60 30,40; 50,10 85,30 85,70 50,90 15,70 15,30; 50,30 70,40 70,60 50,70 30,60 30,40" />
                    </polygon>
                  </svg>
                </div>
              )}
            </div>
          </div>

          {/* WORKFLOW CONNECTOR */}
          <div className="workflow-connector" data-animate>
            <div className="workflow-node"><Download size={16} /> Import</div>
            <div className="pulse-line"></div>
            <div className="workflow-node"><Cpu size={16} /> Automate</div>
            <div className="pulse-line"></div>
            <div className="workflow-node"><ShieldCheck size={16} /> Review</div>
            <div className="pulse-line"></div>
            <div className="workflow-node"><Check size={16} /> Approve</div>
            <div className="pulse-line"></div>
            <div className="workflow-node"><ArrowRight size={16} /> Export</div>
          </div>
          
          <div className="feature-grid">
            <div className="feature-card fade-up" style={{ transitionDelay: "0ms" }}>
              <div className="card-visual">
                <div style={{ position: "relative", width: "120px" }}>
                  <div style={{ position: "absolute", top: "6px", left: "0", width: "100%", height: "1px", background: "rgba(255,255,255,0.1)" }}></div>
                  <div className="pipeline-dot"></div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <div className="pipeline-node" style={{ width: "12px", height: "12px", borderRadius: "50%" }}></div>
                    <div className="pipeline-node" style={{ width: "12px", height: "12px", borderRadius: "50%" }}></div>
                    <div className="pipeline-node" style={{ width: "12px", height: "12px", borderRadius: "50%" }}></div>
                  </div>
                </div>
              </div>
              <div className="icon-wrap"><ShieldCheck size={20} /></div>
              <h3 className="card-title">DPDP Compliance</h3>
              <p className="body-text">Map obligations to workflows. Maintain evidence. Stay ready.</p>
              <div className="replaces-callout">Replaces: legal spreadsheets and consultant-led reviews</div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "11px", color: "#3B82F6", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px" }}>
                Try it in the app &rarr;
              </a>
            </div>
            <div className="feature-card fade-up" style={{ transitionDelay: "80ms" }}>
              <div style={{ height: "80px", width: "100%", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "12px" }}>
                <svg viewBox="0 0 240 80" width="240" height="80" xmlns="http://www.w3.org/2000/svg">
                  <line x1="80" y1="40" x2="120" y2="20" stroke="#1D4ED8" strokeWidth="1" opacity="0.6"/>
                  <line x1="80" y1="40" x2="120" y2="40" stroke="#1D4ED8" strokeWidth="1" opacity="0.6"/>
                  <line x1="80" y1="40" x2="120" y2="60" stroke="#1D4ED8" strokeWidth="1" opacity="0.6"/>
                  <line x1="120" y1="20" x2="160" y2="40" stroke="#0E7490" strokeWidth="1" opacity="0.6"/>
                  <line x1="120" y1="40" x2="160" y2="40" stroke="#0E7490" strokeWidth="1" opacity="0.6"/>
                  <line x1="120" y1="60" x2="160" y2="40" stroke="#0E7490" strokeWidth="1" opacity="0.6"/>

                  <circle cx="80" cy="40" r="14" fill="#0D1A30" stroke="#3B82F6" strokeWidth="2"/>
                  <text x="80" y="37" textAnchor="middle" fill="#3B82F6" fontSize="7" fontFamily="monospace">AI</text>
                  <text x="80" y="46" textAnchor="middle" fill="#3B82F6" fontSize="7" fontFamily="monospace">Model</text>

                  <circle cx="120" cy="20" r="10" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.5"/>
                  <text x="120" y="24" textAnchor="middle" fill="#22D3EE" fontSize="6.5" fontFamily="monospace">Controls</text>

                  <circle cx="120" cy="40" r="10" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.5"/>
                  <text x="120" y="44" textAnchor="middle" fill="#22D3EE" fontSize="6.5" fontFamily="monospace">Owners</text>

                  <circle cx="120" cy="60" r="10" fill="#0D1A30" stroke="#22D3EE" strokeWidth="1.5"/>
                  <text x="120" y="64" textAnchor="middle" fill="#22D3EE" fontSize="6.5" fontFamily="monospace">Docs</text>

                  <circle cx="160" cy="40" r="12" fill="#0D1A30" stroke="#22C55E" strokeWidth="2"/>
                  <text x="160" y="37" textAnchor="middle" fill="#22C55E" fontSize="6" fontFamily="monospace">Audit</text>
                  <text x="160" y="46" textAnchor="middle" fill="#22C55E" fontSize="6" fontFamily="monospace">Ready</text>

                  <circle cx="80" cy="40" r="14" fill="none" stroke="#3B82F6" strokeWidth="1" opacity="0">
                    <animate attributeName="r" values="14;22;14" dur="2.5s" repeatCount="indefinite"/>
                    <animate attributeName="opacity" values="0.6;0;0.6" dur="2.5s" repeatCount="indefinite"/>
                  </circle>
                </svg>
              </div>
              <div className="icon-wrap"><Cpu size={20} /></div>
              <h3 className="card-title">AI Governance</h3>
              <p className="body-text">Document models, accountability, and controls across teams.</p>
              <div className="replaces-callout">Replaces: ad-hoc model registers and email approvals</div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "11px", color: "#3B82F6", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px" }}>
                Try it in the app &rarr;
              </a>
            </div>
            <div className="feature-card fade-up" style={{ transitionDelay: "160ms" }}>
              <div className="card-visual" style={{ alignItems: "flex-end", paddingBottom: "10px" }}>
                <div className="risk-bar" style={{ height: "30%", background: "#EF4444" }}></div>
                <div className="risk-bar" style={{ height: "50%", background: "#F59E0B" }}></div>
                <div className="risk-bar" style={{ height: "80%", background: "#10B981" }}></div>
                <div className="risk-bar" style={{ height: "60%", background: "#3B82F6" }}></div>
              </div>
              <div className="icon-wrap"><BarChart3 size={20} /></div>
              <h3 className="card-title">Risk Assessments</h3>
              <p className="body-text">Track open risks, owners, and remediation cycles in real time.</p>
              <div className="replaces-callout">Replaces: manual trackers with no owner accountability</div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "11px", color: "#3B82F6", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px" }}>
                Try it in the app &rarr;
              </a>
            </div>
            <div className="feature-card fade-up" style={{ transitionDelay: "240ms" }}>
              <div className="card-visual">
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <div className="policy-row" style={{ width: "80px" }}></div>
                  <div className="policy-row" style={{ width: "100px", animationDelay: "1s" }}></div>
                  <div className="policy-row" style={{ width: "80px", animationDelay: "2s" }}></div>
                </div>
              </div>
              <div className="icon-wrap"><FileText size={20} /></div>
              <h3 className="card-title">Policy Management</h3>
              <p className="body-text">Versioned policies tied to real operational controls.</p>
              <div className="replaces-callout">Replaces: shared drives with unversioned Word docs</div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "11px", color: "#3B82F6", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px" }}>
                Try it in the app &rarr;
              </a>
            </div>
            <div className="feature-card fade-up" style={{ transitionDelay: "320ms" }}>
              <div className="card-visual">
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div className="timeline-dot" style={{ animation: "move-dot 3s infinite", opacity: 1 }}></div>
                  <div className="timeline-dot" style={{ animation: "move-dot 3s infinite", animationDelay: "1s", opacity: 1 }}></div>
                  <div className="timeline-dot" style={{ animation: "move-dot 3s infinite", animationDelay: "2s", opacity: 1 }}></div>
                </div>
              </div>
              <div className="icon-wrap"><ClipboardList size={20} /></div>
              <h3 className="card-title">Audit Trails</h3>
              <p className="body-text">Durable record of scans, changes, approvals, and evidence.</p>
              <div className="replaces-callout">Replaces: reconstructing evidence from emails the night before</div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "11px", color: "#3B82F6", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px" }}>
                Try it in the app &rarr;
              </a>
            </div>
            <div className="feature-card fade-up" style={{ transitionDelay: "400ms" }}>
              <div className="card-visual">
                <svg width="40" height="40" viewBox="0 0 100 100">
                  <polygon points="50,5 90,25 90,75 50,95 10,75 10,25" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
                  <polygon points="50,30 70,40 70,60 50,70 30,60 30,40" fill="var(--accent)" fillOpacity="0.3" stroke="var(--accent)" strokeWidth="2">
                    <animate attributeName="points" dur="3s" repeatCount="indefinite" values="50,30 70,40 70,60 50,70 30,60 30,40; 50,10 85,30 85,70 50,90 15,70 15,30; 50,30 70,40 70,60 50,70 30,60 30,40" />
                  </polygon>
                </svg>
              </div>
              <div className="icon-wrap"><Building2 size={20} /></div>
              <h3 className="card-title">Vendor Compliance</h3>
              <p className="body-text">Structured reviews with risk signals, not email threads.</p>
              <div className="replaces-callout">Replaces: questionnaire email threads with no tracking</div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "11px", color: "#3B82F6", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px" }}>
                Try it in the app &rarr;
              </a>
            </div>
          </div>

          {/* OPEN SOURCE CALLOUT */}
          <div style={{ marginTop: "32px", padding: "20px 24px", background: "#0A1626", border: "1px solid #1B3A5C", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }} data-animate>
            <div>
              <p style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "4px" }}>
                🐙 CompliSense-AI is open source.
              </p>
              <p style={{ fontSize: "13px", color: "#64748B" }}>
                Read the code, inspect the rulepacks, and trust what you're deploying.
              </p>
            </div>
            <a href="https://github.com/hardik-goel/CompliSense-AI"
               target="_blank" rel="noopener noreferrer"
               style={{ fontSize: "13px", color: "#3B82F6", border: "1px solid #1B3A5C", padding: "8px 16px", borderRadius: "6px", textDecoration: "none", whiteSpace: "nowrap" }}>
              View on GitHub &rarr;
            </a>
          </div>

          {/* BY THE NUMBERS / CHARTS */}
          <div className="section-header" style={{ marginTop: "96px" }} data-animate>
            <p className="label-caption">BY THE NUMBERS</p>
            <h3>What teams measure after going live.</h3>
          </div>
          
          <div className="charts-grid">
            <div className="chart-card fade-up">
              <h4 className="card-title" style={{ marginBottom: "24px", fontSize: "0.875rem" }}>Time saved per compliance task</h4>
              <div className="bar-row">
                <span className="bar-label">Evidence Collection</span>
                <div className="bar-bg"><div className="bar-fill" style={{ "--percent": "68%" } as any}></div></div>
                <span style={{ color: "var(--success)" }}>-68%</span>
              </div>
              <div className="bar-row">
                <span className="bar-label">Policy Review Cycle</span>
                <div className="bar-bg"><div className="bar-fill" style={{ "--percent": "55%" } as any}></div></div>
                <span style={{ color: "var(--success)" }}>-55%</span>
              </div>
              <div className="bar-row">
                <span className="bar-label">Vendor Questionnaires</span>
                <div className="bar-bg"><div className="bar-fill" style={{ "--percent": "62%" } as any}></div></div>
                <span style={{ color: "var(--success)" }}>-62%</span>
              </div>
              <div className="bar-row">
                <span className="bar-label">Audit Prep Time</span>
                <div className="bar-bg"><div className="bar-fill" style={{ "--percent": "71%" } as any}></div></div>
                <span style={{ color: "var(--success)" }}>-71%</span>
              </div>
              <div className="bar-row">
                <span className="bar-label">Risk Updates</span>
                <div className="bar-bg"><div className="bar-fill" style={{ "--percent": "48%" } as any}></div></div>
                <span style={{ color: "var(--success)" }}>-48%</span>
              </div>
              <p style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "16px" }}>Based on operator self-reported time tracking across pilot customers.</p>
            </div>

            <div className="chart-card fade-up">
              <h4 className="card-title" style={{ marginBottom: "24px", fontSize: "0.875rem", textAlign: "center" }}>Average compliance score after 8 weeks</h4>
              <div className="donut-chart">
                <svg width="120" height="120" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="54" fill="none" stroke="var(--border)" strokeWidth="8" />
                  <circle cx="60" cy="60" r="54" fill="none" stroke="var(--success)" strokeWidth="8" strokeDasharray="339.3" strokeDashoffset="74.6" style={{ transition: "stroke-dashoffset 1.5s ease-out" }} />
                </svg>
                <div className="donut-text">
                  <div style={{ fontSize: "1.5rem", fontWeight: "700" }}>78%</div>
                  <div style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>Week 8 baseline</div>
                </div>
              </div>
              <p style={{ fontSize: "10px", color: "var(--text-muted)", textAlign: "center", marginTop: "16px" }}>Avg. Score at Week 8</p>
            </div>

            <div className="chart-card fade-up">
              <h4 className="card-title" style={{ marginBottom: "24px", fontSize: "0.875rem" }}>Where compliance effort goes</h4>
              <div className="segmented-bar">
                <div className="segment" style={{ width: "38%", background: "var(--accent)" }} title="Evidence 38%">38%</div>
                <div className="segment" style={{ width: "24%", background: "#3B82F6" }} title="Policy 24%">24%</div>
                <div className="segment" style={{ width: "21%", background: "#8B5CF6" }} title="Vendor Reviews 21%">21%</div>
                <div className="segment" style={{ width: "17%", background: "#F59E0B" }} title="Audit Prep 17%">17%</div>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "16px" }}>
                <span style={{ fontSize: "10px", display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "6px", height: "6px", background: "var(--accent)" }}></div> Evidence</span>
                <span style={{ fontSize: "10px", display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "6px", height: "6px", background: "#3B82F6" }}></div> Policy</span>
                <span style={{ fontSize: "10px", display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "6px", height: "6px", background: "#8B5CF6" }}></div> Vendor</span>
                <span style={{ fontSize: "10px", display: "flex", alignItems: "center", gap: "4px" }}><div style={{ width: "6px", height: "6px", background: "#F59E0B" }}></div> Audit</span>
              </div>
              <p style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "16px" }}>CompliSense-AI automates the first three segments entirely.</p>
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
            <div className="step-item fade-up" style={{ transitionDelay: "0ms" }}>
              <div className="step-circle">01</div>
              <h3 className="card-title">Connect</h3>
              <p className="body-text">Import policies, controls, vendors, and documents into one structured workspace.</p>
            </div>
            <div className="step-item fade-up" style={{ transitionDelay: "100ms" }}>
              <div className="step-circle">02</div>
              <h3 className="card-title">Automate</h3>
              <p className="body-text">Generate workflows, evidence collection, and governance operations around your programme.</p>
            </div>
            <div className="step-item fade-up" style={{ transitionDelay: "200ms" }}>
              <div className="step-circle">03</div>
              <h3 className="card-title">Stay Ready</h3>
              <p className="body-text">Continuous monitoring, traceable decisions, and an always-current audit trail.</p>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: "12px", color: "#22D3EE", display: "block", marginTop: "8px" }}>
                &rarr; See your audit trail live
              </a>
            </div>
            <div className="step-item fade-up" style={{ transitionDelay: "300ms" }}>
              <div className="step-circle">04</div>
              <h3 className="card-title">Download & Defend</h3>
              <p className="body-text">Export audit-ready packages: findings PDF, evidence ZIP, and decision log — ready for regulators or investors.</p>
            </div>
          </div>

          <div style={{ margin: '48px 0', maxWidth: '960px', marginLeft: 'auto', marginRight: 'auto' }} className="fade-up">
            <p style={{
              fontSize: '11px', letterSpacing: '2px', color: '#64748B',
              textAlign: 'center', marginBottom: '16px',
            }}>
              WATCH IT IN ACTION
            </p>

            <div style={{
              borderRadius: '16px', overflow: 'hidden',
              border: '1px solid #1B3A5C',
              boxShadow: '0 16px 48px rgba(0,0,0,0.35)',
            }}>
              <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
                <iframe
                  src="https://www.youtube-nocookie.com/embed/PWvqFBSR6h8?rel=0&modestbranding=1&color=white"
                  title="CompliSense-AI — See the platform in action"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  loading="lazy"
                  style={{
                    position: 'absolute', top: 0, left: 0,
                    width: '100%', height: '100%', border: 'none',
                  }}
                />
              </div>
            </div>

            <p style={{
              fontSize: '13px', color: '#64748B', textAlign: 'center', marginTop: '12px',
            }}>
              A complete walkthrough: connect your workspace, run a scan, review findings,
              and export your audit package.
            </p>
          </div>

          {/* LIVE METRICS COUNTER BAR */}
          <div style={{ background: "#0A1626", borderTop: "1px solid #1B3A5C", borderBottom: "1px solid #1B3A5C", padding: "20px 0", margin: "64px 0 0 0" }}>
            <div style={{ maxWidth: "960px", margin: "0 auto", display: "flex", justifyContent: "space-around", flexWrap: "wrap", gap: "16px" }}>
              <div style={{ textAlign: "center" }}>
                <p className="countup" data-target="10" style={{ fontSize: "28px", fontWeight: 800, color: "#3B82F6", fontFamily: "monospace" }}>0</p>
                <p style={{ fontSize: "11px", color: "#64748B", marginTop: "2px" }}>Scans/month &middot; Free tier limit</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p className="countup" data-target="6" style={{ fontSize: "28px", fontWeight: 800, color: "#22D3EE", fontFamily: "monospace" }}>0</p>
                <p style={{ fontSize: "11px", color: "#64748B", marginTop: "2px" }}>Compliance modules live</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p className="countup" data-target="2" style={{ fontSize: "28px", fontWeight: 800, color: "#8B5CF6", fontFamily: "monospace" }}>0</p>
                <p style={{ fontSize: "11px", color: "#64748B", marginTop: "2px" }}>Regulatory frameworks</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: "28px", fontWeight: 800, color: "#F59E0B", fontFamily: "monospace" }}>48h</p>
                <p style={{ fontSize: "11px", color: "#64748B", marginTop: "2px" }}>Demo response SLA</p>
              </div>
            </div>
          </div>

          {/* TECHNICAL FLOW DIAGRAM */}
          <div className="section-header" style={{ marginTop: "96px" }} data-animate>
            <p className="label-caption">FOR ENGINEERS</p>
            <h2 style={{ margin: "12px 0" }}>How the local agent works.</h2>
            <p className="body-text">Your evidence never leaves your machine — here's exactly why.</p>
          </div>
          <div className="tech-flow-grid" data-animate>
            <div className="tech-card blue">
              <h4>Your Machine</h4>
              <p>📂 Docs</p>
              <p>🗄 Configs</p>
              <p>📋 Policies</p>
              <div style={{ marginTop: "16px", color: "var(--success)", fontWeight: "700" }}>[stays here]</div>
            </div>
            <div className="tech-arrow">&rarr;</div>
            <div className="tech-card cyan">
              <h4>CompliSense Agent</h4>
              <p>🔍 Scans locally</p>
              <p>⚙ Applies rulepacks</p>
              <p>📝 Generates findings</p>
              <div style={{ marginTop: "16px", color: "var(--success)", fontWeight: "700" }}>[stays here]</div>
            </div>
            <div className="tech-arrow">&rarr;</div>
            <div className="tech-card violet">
              <h4>Secure API</h4>
              <p>📤 Sends metadata</p>
              <p>🔒 JWT auth</p>
              <p>🌐 TLS only</p>
              <div style={{ marginTop: "16px", color: "var(--accent)", fontWeight: "700" }}>[metadata only]</div>
            </div>
            <div className="tech-arrow">&rarr;</div>
            <div className="tech-card green">
              <h4>Dashboard</h4>
              <p>📊 Shows findings</p>
              <p>✓ No raw files</p>
              <p>✓ Audit ready</p>
              <div style={{ marginTop: "16px", color: "var(--success)", fontWeight: "700" }}>[visible here]</div>
            </div>
          </div>
          <div style={{ textAlign: "center", marginTop: "24px", fontSize: "11px", color: "var(--text-muted)" }}>
            Raw files: <span style={{ color: "#EF4444" }}>✗ never transmitted</span> &middot; Metadata: <span style={{ color: "var(--success)" }}>✓ encrypted in transit</span> &middot; Credentials: <span style={{ color: "#EF4444" }}>✗ never stored</span>
          </div>

          <div className="section-header" style={{ marginTop: "96px" }} data-animate>
            <h2>Built for engineers. Trusted by compliance leads.</h2>
          </div>
          <div className="arch-grid">
            <div className="arch-card fade-up">
              <span className="arch-label">Local Agent</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Evidence stays local</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>The collection agent runs on your machine. No raw data ever leaves your environment.</p>
            </div>
            <div className="arch-card fade-up" style={{ transitionDelay: "100ms" }}>
              <span className="arch-label">SaaS Dashboard</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Centralised insights</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Scan metadata, findings, and audit trails sync to a hosted dashboard. Inspect anywhere.</p>
            </div>
            <div className="arch-card fade-up" style={{ transitionDelay: "200ms" }}>
              <span className="arch-label">API-First</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Programmable flows</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Every action is API-accessible. Integrate with CI/CD, Slack, or JIRA seamlessly.</p>
            </div>
            <div className="arch-card fade-up" style={{ transitionDelay: "300ms" }}>
              <span className="arch-label">Rulepack Model</span>
              <h3 className="card-title" style={{ marginBottom: "8px" }}>Market Agnostic</h3>
              <p className="body-text" style={{ fontSize: "0.85rem" }}>Compliance logic is versioned rulepacks. Switch markets without changing code.</p>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST BANNER */}
      <section id="privacy-usp" className="fade-up">
        <div className="container">
          <div className="trust-banner">
            <div className="trust-icon">🔒</div>
            <div className="trust-content">
              <h2>Your data never leaves your machine.</h2>
              <p className="body-text" style={{ color: "var(--text-secondary)", marginTop: "12px" }}>
                CompliSense-AI's evidence collection agent runs locally on your infrastructure.
                Only scan findings and metadata sync to the dashboard — never raw documents,
                never source files, never credentials.
              </p>
            </div>
            <div className="trust-badges">
              <div className="framework-badge">Local Agent</div>
              <div className="framework-badge">Metadata Only</div>
              <div className="framework-badge">Zero Raw Upload</div>
              <div className="framework-badge">JWT Auth</div>
            </div>
          </div>
        </div>
      </section>

      {/* METRICS / IMPACT SECTION */}
      <section className="metrics-band" id="impact">
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
            <div className="testimonial-card fade-up">
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
            <div className="testimonial-card fade-up" style={{ transitionDelay: "100ms" }}>
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
            <div className="testimonial-card fade-up" style={{ transitionDelay: "200ms" }}>
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

      {/* CREDIBILITY BAR */}
      <div className="container">
        <div className="credibility-bar" data-animate>
          <span className="cred-item">🎤 Mentioned at ElasticSearch CXO Fusion</span>
          <span className="divider">·</span>
          <a href="https://medium.com/@hardik.goel214" target="_blank" rel="noopener noreferrer" className="cred-item">📰 Featured on Medium</a>
          <span className="divider">·</span>
          <a href="https://github.com/hardik-goel/CompliSense-AI" target="_blank" rel="noopener noreferrer" className="cred-item">🐙 Open source on GitHub</a>
          <span className="divider">·</span>
          <span className="cred-item">🇮🇳 Built in India</span>
        </div>
      </div>

      {/* FOUNDER SECTION */}
      <section id="founder" style={{ padding: "80px 0" }} className="content-section">
        <div className="container">
          <p style={{ fontSize: "11px", letterSpacing: "2px", color: "#64748B", textAlign: "center", marginBottom: "8px" }} data-animate>THE TEAM</p>
          <h2 style={{ textAlign: "center", fontSize: "32px", fontWeight: 800, color: "#F1F5F9", marginBottom: "48px" }} data-animate>
            Built by people who've been in the compliance room.
          </h2>

          <div style={{ maxWidth: "640px", margin: "0 auto", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "16px", padding: "36px", display: "flex", gap: "28px", alignItems: "flex-start" }} className="fade-up">
            <div style={{ width: "72px", height: "72px", borderRadius: "50%", background: "linear-gradient(135deg,#1D4ED8,#0E7490)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "24px", fontWeight: 800, color: "#fff", flexShrink: 0 }}>
              HG
            </div>
            <div>
              <p style={{ fontSize: "18px", fontWeight: 700, color: "#F1F5F9", marginBottom: "2px" }}>Hardik Goel</p>
              <p style={{ fontSize: "13px", color: "#3B82F6", marginBottom: "16px" }}>Founder &middot; Technical Architect, SDE3 @ Tesco</p>
              <p style={{ fontSize: "14px", color: "#94A3B8", lineHeight: 1.8, marginBottom: "20px" }}>
                13+ years building data platforms, AI systems, and compliance infrastructure at scale.
                Formerly at Paytm, Impetus, Cognizant, and Accenture. Published author.
                Built CompliSense-AI after watching too many teams rebuild compliance evidence from scratch — every single audit cycle.
              </p>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <a href="https://www.linkedin.com/in/hardik-goel-a6334936" target="_blank" rel="noopener noreferrer" style={{ fontSize: "12px", color: "#3B82F6", textDecoration: "none", border: "1px solid #1B3A5C", padding: "6px 14px", borderRadius: "6px" }}>
                  LinkedIn &rarr;
                </a>
                <a href="https://medium.com/@hardik.goel214" target="_blank" rel="noopener noreferrer" style={{ fontSize: "12px", color: "#64748B", textDecoration: "none", border: "1px solid #1B3A5C", padding: "6px 14px", borderRadius: "6px" }}>
                  Medium &rarr;
                </a>
                <a href="https://goelh.substack.com" target="_blank" rel="noopener noreferrer" style={{ fontSize: "12px", color: "#64748B", textDecoration: "none", border: "1px solid #1B3A5C", padding: "6px 14px", borderRadius: "6px" }}>
                  Substack &rarr;
                </a>
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

      {/* PRICING SECTION */}
      <section className="content-section" id="pricing">
        <div className="container">
          <div className="section-header" style={{ textAlign: "center" }} data-animate>
            <p className="label-caption">PRICING</p>
            <h2 style={{ margin: "12px 0" }}>Simple to start. Scales with your programme.</h2>
            <p className="body-text">Free to explore. Contact us when you're ready to operationalise.</p>
          </div>

          <div className="pricing-grid">
            {/* Free */}
            <div className="pricing-card fade-up">
              <h3 style={{ fontSize: "1.5rem", marginBottom: "8px" }}>Free</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "16px" }}>Devs & small teams evaluating</p>
              <div style={{ fontSize: "2rem", fontWeight: "700", marginBottom: "24px" }}>£0 <span style={{ fontSize: "1rem", color: "var(--text-muted)" }}>/ Free</span></div>
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "24px", marginBottom: "24px" }}>
                <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.875rem", display: "flex", flexDirection: "column", gap: "12px" }}>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> 10 Scans / month</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Compliance Score</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Artifact Compliance</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Failed Rule Details (Limited)</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— Remediation Guidance</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— Extended Rules</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— Team / RBAC</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— On-prem / VPC</li>
                </ul>
              </div>
              <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ marginTop: "auto" }}>Launch App</a>
            </div>

            {/* Standard */}
            <div className="pricing-card popular fade-up">
              <div className="popular-badge">Most Popular</div>
              <h3 style={{ fontSize: "1.5rem", marginBottom: "8px" }}>Standard</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "16px" }}>Teams working toward compliance</p>
              <div style={{ fontSize: "2rem", fontWeight: "700", marginBottom: "24px" }}>Contact us</div>
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "24px", marginBottom: "24px" }}>
                <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.875rem", display: "flex", flexDirection: "column", gap: "12px" }}>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Unlimited Scans (planned)</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Compliance Score</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Remediation Guidance</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Extended Rules (Art. 12,17,19)</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Email Notifications</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Basic Analytics</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— Bias / Fairness Evaluator</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— Team / RBAC</li>
                </ul>
              </div>
              <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ marginTop: "auto" }}>Book a Demo</a>
            </div>

            {/* Premium */}
            <div className="pricing-card enterprise fade-up">
              <h3 style={{ fontSize: "1.5rem", marginBottom: "8px" }}>Premium</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "16px" }}>Orgs with high regulatory exposure</p>
              <div style={{ fontSize: "2rem", fontWeight: "700", marginBottom: "24px" }}>Contact us</div>
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "24px", marginBottom: "24px" }}>
                <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.875rem", display: "flex", flexDirection: "column", gap: "12px" }}>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Everything in Standard</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Rich Scan History & Analytics</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Bias / Fairness Evaluator</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Explainability Evaluator</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Drift & Robustness Checks</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Team / RBAC</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— SSO</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>— On-prem / VPC</li>
                </ul>
              </div>
              <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ marginTop: "auto" }}>Book a Demo</a>
            </div>

            {/* Premium+ */}
            <div className="pricing-card enterprise fade-up">
              <h3 style={{ fontSize: "1.5rem", marginBottom: "8px" }}>Premium+</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "16px" }}>Enterprise</p>
              <div style={{ fontSize: "2rem", fontWeight: "700", marginBottom: "24px" }}>Contact us</div>
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "24px", marginBottom: "24px" }}>
                <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.875rem", display: "flex", flexDirection: "column", gap: "12px" }}>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Everything in Premium</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> SSO & Multi-tenant</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> Private Rulepacks</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> On-prem / VPC</li>
                  <li style={{ display: "flex", alignItems: "center", gap: "8px" }}><Check size={14} className="status-check" /> SLA + Dedicated Support</li>
                </ul>
              </div>
              <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ marginTop: "auto" }}>Contact Sales</a>
            </div>
          </div>

          <div style={{ marginTop: "64px" }}>
            <details style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden" }}>
              <summary style={{ padding: "20px 24px", cursor: "pointer", fontWeight: "600", fontSize: "0.875rem" }}>
                See full comparison &rarr;
              </summary>
              <div className="comparison-wrap" style={{ border: "none", marginTop: 0 }}>
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Feature</th>
                      <th>Free</th>
                      <th>Standard</th>
                      <th>Premium</th>
                      <th>Premium+</th>
                    </tr>
                  </thead>
                  <tbody style={{ fontSize: "0.8125rem" }}>
                    <tr><td>Scans / month</td><td>10</td><td>Unlimited (planned)</td><td>Unlimited</td><td>Unlimited</td></tr>
                    <tr><td>Compliance Score</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Artifact Compliance</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Failed Rule Details</td><td>Limited</td><td>✓</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Remediation Guidance</td><td>—</td><td>✓</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Extended Rules (Art. 12,17,19)</td><td>—</td><td>✓</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Scan History & Analytics</td><td>—</td><td>Basic</td><td>Rich</td><td>✓</td></tr>
                    <tr><td>Email Notifications</td><td>—</td><td>✓</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Bias / Fairness Evaluator</td><td>—</td><td>—</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Explainability Evaluator</td><td>—</td><td>—</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Drift & Robustness Checks</td><td>—</td><td>—</td><td>✓</td><td>✓</td></tr>
                    <tr><td>Team / RBAC</td><td>—</td><td>—</td><td>✓</td><td>✓</td></tr>
                    <tr><td>SSO</td><td>—</td><td>—</td><td>—</td><td>✓</td></tr>
                    <tr><td>Multi-tenant</td><td>—</td><td>—</td><td>—</td><td>✓</td></tr>
                    <tr><td>Private Rulepacks</td><td>—</td><td>—</td><td>—</td><td>✓</td></tr>
                    <tr><td>On-prem / VPC</td><td>—</td><td>—</td><td>—</td><td>✓</td></tr>
                    <tr><td>SLA + Dedicated Support</td><td>—</td><td>—</td><td>—</td><td>✓</td></tr>
                    <tr><td>MongoDB required</td><td>No</td><td>Yes</td><td>Yes</td><td>Yes</td></tr>
                  </tbody>
                </table>
              </div>
            </details>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "16px", textAlign: "center", lineHeight: "1.6" }}>
              Standard, Premium, and Premium+ are currently in development. Pricing will be announced alongside general availability.<br/>
              Early access teams get founder pricing — book a call to lock in rates.
            </p>
          </div>
        </div>
      </section>

      {/* ROADMAP TRANSPARENCY STRIP */}
      <section style={{ padding: "48px 0", borderTop: "1px solid #1B3A5C" }} className="content-section">
        <div className="container">
          <p style={{ fontSize: "11px", letterSpacing: "2px", color: "#64748B", textAlign: "center", marginBottom: "8px" }} data-animate>ROADMAP</p>
          <h3 style={{ fontSize: "22px", fontWeight: 700, color: "#F1F5F9", textAlign: "center", marginBottom: "32px" }} data-animate>
            What's coming next.
          </h3>

          <div style={{ maxWidth: "800px", margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }} className="fade-up">
            <div style={{ padding: "20px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "10px", borderLeft: "3px solid #22C55E" }}>
              <p style={{ fontSize: "10px", color: "#22C55E", letterSpacing: "1px", marginBottom: "6px" }}>LIVE NOW</p>
              <p style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "4px" }}>Free Tier — Full EU AI Act & DPDP Core</p>
              <p style={{ fontSize: "12px", color: "#64748B" }}>10 scans/month. No credit card. Start today.</p>
            </div>

            <div style={{ padding: "20px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "10px", borderLeft: "3px solid #3B82F6" }}>
              <p style={{ fontSize: "10px", color: "#3B82F6", letterSpacing: "1px", marginBottom: "6px" }}>IN DEVELOPMENT</p>
              <p style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "4px" }}>Standard Tier — Remediation + History</p>
              <p style={{ fontSize: "12px", color: "#64748B" }}>Step-by-step fixes + scan history. Coming Q3 2026.</p>
            </div>

            <div style={{ padding: "20px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "10px", borderLeft: "3px solid #8B5CF6" }}>
              <p style={{ fontSize: "10px", color: "#8B5CF6", letterSpacing: "1px", marginBottom: "6px" }}>PLANNED</p>
              <p style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "4px" }}>Premium — Bias, Drift & Team RBAC</p>
              <p style={{ fontSize: "12px", color: "#64748B" }}>Advanced evaluators for high-risk AI systems.</p>
            </div>

            <div style={{ padding: "20px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "10px", borderLeft: "3px solid #F59E0B" }}>
              <p style={{ fontSize: "10px", color: "#F59E0B", letterSpacing: "1px", marginBottom: "6px" }}>ENTERPRISE</p>
              <p style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "4px" }}>Premium+ — SSO, On-Prem & White-Glove</p>
              <p style={{ fontSize: "12px", color: "#64748B" }}>Private rulepacks, VPC, dedicated support.</p>
            </div>
          </div>

          <p style={{ textAlign: "center", marginTop: "24px" }} data-animate>
            <a href="https://github.com/hardik-goel/CompliSense-AI"
               target="_blank" rel="noopener noreferrer"
               style={{ fontSize: "13px", color: "#3B82F6" }}>
              Follow development on GitHub &rarr;
            </a>
          </p>
        </div>
      </section>

      {/* JOIN THE EARLY ACCESS PROGRAMME */}
      <section className="content-section" style={{ background: "rgba(37, 99, 235, 0.05)" }}>
        <div className="container">
          <div className="section-header" style={{ textAlign: "center" }} data-animate>
            <p className="label-caption">EARLY ACCESS</p>
            <h2 style={{ margin: "12px 0" }}>Be among the first operators to go live.</h2>
            <p className="body-text">We're onboarding teams in waves. Leave your details and we'll reach out within 48 hours.</p>
          </div>
          
          <div style={{ maxWidth: "640px", margin: "48px auto" }} className="fade-up">
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const email = formData.get("email");
                const company = formData.get("company");
                window.location.href = `mailto:${supportEmail}?subject=Early Access Request&body=Email: ${email}%0D%0ACompany: ${company}`;
                alert("Thank you! Opening your email client to send the request.");
              }}
              style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}
            >
              <input 
                name="email" 
                type="email" 
                placeholder="Work Email" 
                required 
                style={{ flex: 1, minWidth: "200px", padding: "12px 16px", borderRadius: "8px", border: "1px solid var(--border)", background: "var(--surface)", color: "white" }} 
              />
              <input 
                name="company" 
                type="text" 
                placeholder="Company" 
                required 
                style={{ flex: 1, minWidth: "200px", padding: "12px 16px", borderRadius: "8px", border: "1px solid var(--border)", background: "var(--surface)", color: "white" }} 
              />
              <button type="submit" className="btn-primary" style={{ width: "fit-content" }}>Get Early Access &rarr;</button>
            </form>
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
            <p className="body-text">Want to know more? <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)", fontWeight: "600" }}>Book a 30-minute call &rarr;</a></p>
          </div>
        </div>
      </section>

      {/* CTA / CONTACT SECTION */}
      <section className="content-section" id="contact" style={{ paddingBottom: 0 }}>
        <div className="container">
          <div className="cta-section" data-animate>
            <h2>Ready to centralise your compliance operations?</h2>
            <p>Book a 30-minute demo. See the platform live.</p>
            <div className="cta-actions" style={{ flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
                <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">
                  📅 Book a 30-min Demo
                </a>
                <a href="https://www.linkedin.com/company/complisense-ai" target="_blank" rel="noopener noreferrer" className="btn-ghost">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: "6px", verticalAlign: "middle" }}>
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  Connect on LinkedIn
                </a>
              </div>
              <a href={`mailto:${supportEmail}?subject=CompliSense-AI%20Enquiry`}
                 style={{ fontSize: "12px", color: "#64748B", textDecoration: "underline", display: "block", marginTop: "8px", textAlign: "center" }}>
                or email us directly
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* FLOATING CTA */}
      <a id="floating-cta" href={appUrl} target="_blank" rel="noopener noreferrer">
        ⚡ Launch App
      </a>

      {/* FOOTER */}
      <footer className="site-footer">
        <div className="container">
          <div className="footer-top">
            <div className="footer-brand">
              <img src="/logo.png" alt="CompliSense-AI" style={{ height: "36px", marginBottom: "16px", objectFit: "contain" }} />
              <p>AI-native compliance for modern teams — built for India's regulatory moment, designed for the operators who can't afford to get it wrong.</p>
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
              <a href="#impact">Impact</a>
              <a href="/changelog" style={{ fontSize: "13px", color: "#64748B", textDecoration: "none" }}>Changelog</a>
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
            <a href={`mailto:${supportEmail}`} style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "underline" }}>{supportEmail}</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
