import Link from "next/link";
import { ArrowRight, Check, ShieldCheck, Cpu, BarChart3, FileText, ClipboardList, Building2 } from "lucide-react";

export const metadata = {
  title: 'Changelog · CompliSense-AI',
  description: 'Release notes and product updates for CompliSense-AI.',
};

const appUrl = "https://app.complisenseai.com";

export default function ChangelogPage() {
  return (
    <main className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand">
            <img src="/logo.png" alt="CompliSense-AI" className="brand-logo" style={{ height: "44px", width: "auto", objectFit: "contain" }} />
          </Link>
          <div className="header-actions">
            <Link className="button button-ghost" href="/">Back to Home</Link>
            <a href={appUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">Launch App &rarr;</a>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "80px 24px 120px" }}>
        <nav style={{ fontSize: "12px", color: "#64748B", marginBottom: "32px" }}>
          <Link href="/" style={{ color: "#3B82F6" }}>Home</Link> / Changelog
        </nav>

        <div style={{ marginBottom: "48px", paddingBottom: "32px", borderBottom: "1px solid #1B3A5C" }}>
          <p style={{ fontSize: "11px", letterSpacing: "2px", color: "#3B82F6", marginBottom: "8px" }}>PRODUCT UPDATES</p>
          <h1 style={{ fontSize: "36px", fontWeight: 800, color: "#F1F5F9", marginBottom: "12px" }}>Changelog</h1>
          <p style={{ color: "#94A3B8", fontSize: "14px" }}>What's shipped, what's fixed, what's next.</p>
        </div>

        <div className="changelog-list" style={{ borderLeft: "2px solid #1B3A5C", marginLeft: "12px", paddingLeft: "32px" }}>
          
          {/* RELEASE v0.4.0 */}
          <div style={{ position: "relative", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px", padding: "24px 28px", marginBottom: "32px" }}>
            <div style={{ position: "absolute", left: "-39px", top: "28px", width: "12px", height: "12px", borderRadius: "50%", background: "#22C55E", border: "2px solid #07111F" }}></div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px", flexWrap: "wrap" }}>
              <span style={{ fontFamily: "monospace", fontSize: "12px", fontWeight: 700, color: "#22C55E", background: "rgba(34,197,94,0.1)", padding: "2px 8px", borderRadius: "4px" }}>v0.4.0</span>
              <span style={{ fontSize: "12px", color: "#64748B" }}>June 2026</span>
              <span style={{ fontSize: "11px", color: "#22C55E", background: "rgba(34,197,94,0.1)", padding: "2px 8px", borderRadius: "4px" }}>Feature</span>
            </div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#F1F5F9", marginBottom: "16px" }}>EU AI Act Extended + DPDP Core rulepacks live</h3>
            <ul style={{ color: "#94A3B8", paddingLeft: "20px", margin: 0, fontSize: "14px", lineHeight: 1.8 }}>
              <li>Added EU AI Act Extended coverage (Art. 12, 17, 19 obligations)</li>
              <li>DPDP India Core rulepack — all Sections mapped to evidence requirements</li>
              <li>Improved scan result grouping by article and risk tier</li>
              <li>Dashboard now shows per-article readiness percentage</li>
              <li>Free tier scan limit enforced server-side (10 scans/month)</li>
            </ul>
          </div>

          {/* RELEASE v0.3.0 */}
          <div style={{ position: "relative", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px", padding: "24px 28px", marginBottom: "32px" }}>
            <div style={{ position: "absolute", left: "-39px", top: "28px", width: "12px", height: "12px", borderRadius: "50%", background: "#3B82F6", border: "2px solid #07111F" }}></div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px", flexWrap: "wrap" }}>
              <span style={{ fontFamily: "monospace", fontSize: "12px", fontWeight: 700, color: "#3B82F6", background: "rgba(59,130,246,0.1)", padding: "2px 8px", borderRadius: "4px" }}>v0.3.0</span>
              <span style={{ fontSize: "12px", color: "#64748B" }}>May 2026</span>
              <span style={{ fontSize: "11px", color: "#3B82F6", background: "rgba(59,130,246,0.1)", padding: "2px 8px", borderRadius: "4px" }}>Feature</span>
            </div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#F1F5F9", marginBottom: "16px" }}>Vendor Compliance module + Audit Trail export</h3>
            <ul style={{ color: "#94A3B8", paddingLeft: "20px", margin: 0, fontSize: "14px", lineHeight: 1.8 }}>
              <li>Vendor questionnaire workflow — structured reviews with risk scoring</li>
              <li>Audit trail now exportable as PDF + JSON</li>
              <li>Evidence collection agent: v0.3 with improved artifact detection</li>
              <li>Added support for scanning additional document types (.md, .rst, .txt)</li>
              <li>Bug fix: scan timeout on large repositories resolved</li>
            </ul>
          </div>

          {/* RELEASE v0.2.0 */}
          <div style={{ position: "relative", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px", padding: "24px 28px", marginBottom: "32px" }}>
            <div style={{ position: "absolute", left: "-39px", top: "28px", width: "12px", height: "12px", borderRadius: "50%", background: "#3B82F6", border: "2px solid #07111F" }}></div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px", flexWrap: "wrap" }}>
              <span style={{ fontFamily: "monospace", fontSize: "12px", fontWeight: 700, color: "#3B82F6", background: "rgba(59,130,246,0.1)", padding: "2px 8px", borderRadius: "4px" }}>v0.2.0</span>
              <span style={{ fontSize: "12px", color: "#64748B" }}>April 2026</span>
              <span style={{ fontSize: "11px", color: "#3B82F6", background: "rgba(59,130,246,0.1)", padding: "2px 8px", borderRadius: "4px" }}>Feature</span>
            </div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#F1F5F9", marginBottom: "16px" }}>Policy Management + Risk Assessment workflows</h3>
            <ul style={{ color: "#94A3B8", paddingLeft: "20px", margin: 0, fontSize: "14px", lineHeight: 1.8 }}>
              <li>Policy versioning — track changes, owners, and approval status</li>
              <li>Risk register: open risks with owner assignment and remediation cycles</li>
              <li>Improved onboarding flow — workspace setup in under 10 minutes</li>
              <li>MongoDB integration for scan history (optional, Standard tier)</li>
              <li>UI: dark theme refinements across all dashboard views</li>
            </ul>
          </div>

          {/* RELEASE v0.1.0 */}
          <div style={{ position: "relative", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px", padding: "24px 28px", marginBottom: "32px" }}>
            <div style={{ position: "absolute", left: "-39px", top: "28px", width: "12px", height: "12px", borderRadius: "50%", background: "#8B5CF6", border: "2px solid #07111F" }}></div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px", flexWrap: "wrap" }}>
              <span style={{ fontFamily: "monospace", fontSize: "12px", fontWeight: 700, color: "#8B5CF6", background: "rgba(139,92,246,0.1)", padding: "2px 8px", borderRadius: "4px" }}>v0.1.0</span>
              <span style={{ fontSize: "12px", color: "#64748B" }}>March 2026</span>
              <span style={{ fontSize: "11px", color: "#8B5CF6", background: "rgba(139,92,246,0.1)", padding: "2px 8px", borderRadius: "4px" }}>Release</span>
            </div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#F1F5F9", marginBottom: "16px" }}>Initial release — EU AI Act core scanning</h3>
            <ul style={{ color: "#94A3B8", paddingLeft: "20px", margin: 0, fontSize: "14px", lineHeight: 1.8 }}>
              <li>Core compliance scanner: EU AI Act articles 9, 10, 13, 14, 15</li>
              <li>Local evidence collection agent (Python, runs on-machine)</li>
              <li>Basic dashboard: overall compliance %, artifact coverage, rule breakdown</li>
              <li>Free tier: 10 scans/month, no credit card required</li>
              <li>Open source under MIT licence</li>
            </ul>
          </div>

        </div>

        <div style={{ marginTop: "48px", padding: "24px", background: "#0E1E33", border: "1px solid #1B3A5C", borderRadius: "12px", textAlign: "center" }}>
          <p style={{ fontSize: "14px", color: "#94A3B8", marginBottom: "16px" }}>
            Want to follow development in real time?
          </p>
          <a href="https://github.com/hardik-goel/CompliSense-AI"
             target="_blank" rel="noopener noreferrer"
             style={{ fontSize: "13px", color: "#3B82F6", border: "1px solid #1B3A5C", padding: "8px 20px", borderRadius: "6px", textDecoration: "none", marginRight: "12px", display: "inline-block", marginBottom: "8px" }}>
            ⭐ Star on GitHub
          </a>
          <a href="https://calendly.com/hardik-goel214/complisense-ai"
             target="_blank" rel="noopener noreferrer"
             style={{ fontSize: "13px", color: "#fff", background: "#3B82F6", padding: "8px 20px", borderRadius: "6px", textDecoration: "none", display: "inline-block", marginBottom: "8px" }}>
            📅 Book a Demo
          </a>
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