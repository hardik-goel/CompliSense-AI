"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ShieldCheck, FileText, Check, Cpu, Package, ClipboardList } from "lucide-react";

const STEPS = ["Connect", "Scan", "Review", "Export"] as const;

/** Long enough to actually read a panel before it moves on. */
const DWELL_MS = 6000;

export default function ProductShowcase({ showCaption = true }: { showCaption?: boolean }) {
  const [showcaseStep, setShowcaseStep] = useState(0); // 0: Connect, 1: Scan, 2: Review, 3: Export
  // A manual selection ends autoplay for the session; hover/focus only suspends it.
  const [autoplay, setAutoplay] = useState(true);
  const [suspended, setSuspended] = useState(false);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!autoplay || suspended || reduced) return;
    const timer = setInterval(() => {
      setShowcaseStep((prev) => (prev + 1) % STEPS.length);
    }, DWELL_MS);
    return () => clearInterval(timer);
  }, [autoplay, suspended]);

  const selectStep = useCallback((i: number) => {
    setShowcaseStep(i);
    setAutoplay(false);
  }, []);

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>, i: number) => {
      const last = STEPS.length - 1;
      let next: number | null = null;
      if (e.key === "ArrowRight") next = i === last ? 0 : i + 1;
      else if (e.key === "ArrowLeft") next = i === 0 ? last : i - 1;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = last;
      if (next === null) return;
      e.preventDefault();
      selectStep(next);
      tabRefs.current[next]?.focus();
    },
    [selectStep],
  );

  const scene = (i: number) => ({
    id: `showcase-panel-${i}`,
    role: "tabpanel" as const,
    "aria-labelledby": `showcase-tab-${i}`,
    "aria-hidden": showcaseStep !== i,
    className: `scene ${showcaseStep === i ? "active" : ""}`,
  });

  return (
    <>
      <div className="showcase">
        <div className="showcase-chrome">
          <div className="chrome-dots">
            <span style={{ background: "#EF4444" }}></span>
            <span style={{ background: "#F59E0B" }}></span>
            <span style={{ background: "#22C55E" }}></span>
          </div>
          <div className="chrome-url">
            <ShieldCheck size={12} /> app.complisenseai.com
          </div>
          <div className="chrome-live"><span className="live-dot"></span> Live</div>
        </div>

        <div
          className="showcase-stage"
          onMouseEnter={() => setSuspended(true)}
          onMouseLeave={() => setSuspended(false)}
        >
          {/* SCENE 0 — CONNECT */}
          <div {...scene(0)}>
            <div className="scene-head">
              <span className="scene-kicker">Step 01 · Connect</span>
              <h4>Import your workspace</h4>
            </div>
            <div className="doc-grid">
              {[
                { n: "Privacy_Policy.pdf", t: "Policy" },
                { n: "DPA_Vendor_AWS.docx", t: "Vendor" },
                { n: "Model_Card_v3.md", t: "AI Model" },
                { n: "Consent_Flow.json", t: "Config" },
                { n: "DPIA_2026.pdf", t: "Risk" },
                { n: "Retention_Schedule.xlsx", t: "Policy" },
              ].map((d, i) => (
                <div className="doc-chip" key={d.n} style={{ animationDelay: `${i * 0.12}s` }}>
                  <FileText size={14} />
                  <div className="doc-meta">
                    <span className="doc-name">{d.n}</span>
                    <span className="doc-type">{d.t}</span>
                  </div>
                  <Check size={13} className="doc-tick" />
                </div>
              ))}
            </div>
            <div className="scene-foot">
              <Check size={13} className="status-check" /> 6 of 12 artefacts mapped — no raw files uploaded
            </div>
          </div>

          {/* SCENE 1 — SCAN */}
          <div {...scene(1)}>
            <div className="scene-head">
              <span className="scene-kicker">Step 02 · Scan</span>
              <h4>Run against live rulepacks</h4>
            </div>
            <div className="scan-feed">
              <div className="scan-feed-line"><Cpu size={13} /> Checking DPDP India · Core obligations…</div>
              <div className="scan-feed-line"><Cpu size={13} /> Checking EU AI Act · Art. 9, 13, 15…</div>
              <div className="scan-feed-line"><Cpu size={13} /> Cross-referencing vendor questionnaires…</div>
              <div className="scan-feed-line dim"><Cpu size={13} /> Compiling evidence index…</div>
            </div>
            <div className="scan-meter">
              <div className="scan-meter-track"><div className="scan-meter-fill"></div></div>
              <div className="scan-meter-labels">
                <span>Scanning 248 controls</span>
                <span className="scan-pct">67%</span>
              </div>
            </div>
          </div>

          {/* SCENE 2 — REVIEW */}
          <div {...scene(2)}>
            <div className="scene-head">
              <span className="scene-kicker">Step 03 · Review</span>
              <h4>Findings, scored and owned</h4>
            </div>
            <div className="review-layout">
              <div className="review-list">
                <div className="review-row"><span>EU AI Act · Art. 9 — Transparency</span><span className="badge-pass">PASS</span></div>
                <div className="review-row"><span>DPDP Core — DPO assignment</span><span className="badge-partial">PARTIAL</span></div>
                <div className="review-row"><span>Vendor questionnaire — 3 gaps</span><span className="badge-action">ACTION</span></div>
                <div className="review-row"><span>Retention policy — versioned</span><span className="badge-pass">PASS</span></div>
              </div>
              <div className="review-score">
                <svg width="104" height="104" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="52" fill="none" stroke="var(--border)" strokeWidth="9" />
                  <circle className="score-arc" cx="60" cy="60" r="52" fill="none" stroke="var(--success)" strokeWidth="9" strokeLinecap="round" strokeDasharray="326.7" strokeDashoffset="71.8" transform="rotate(-90 60 60)" />
                </svg>
                <div className="review-score-text">
                  <strong>78%</strong>
                  <span>Readiness</span>
                </div>
              </div>
            </div>
          </div>

          {/* SCENE 3 — EXPORT */}
          <div {...scene(3)}>
            <div className="scene-head">
              <span className="scene-kicker">Step 04 · Export</span>
              <h4>Audit package, ready to defend</h4>
            </div>
            <div className="export-grid">
              <div className="export-card"><FileText size={18} /><span>Findings_Report.pdf</span><em>Regulator-ready</em></div>
              <div className="export-card"><Package size={18} /><span>Evidence_Bundle.zip</span><em>Traceable artefacts</em></div>
              <div className="export-card"><ClipboardList size={18} /><span>Decision_Log.csv</span><em>Immutable trail</em></div>
            </div>
            <div className="scene-foot success">
              <Check size={13} className="status-check" /> Generated in 4.2s · Next scan auto-runs in 7 days
            </div>
          </div>
        </div>

        {/* STEP RAIL */}
        <div
          className="showcase-rail"
          role="tablist"
          aria-label="Product walkthrough steps"
          onMouseEnter={() => setSuspended(true)}
          onMouseLeave={() => setSuspended(false)}
        >
          {STEPS.map((label, i) => (
            <button
              key={label}
              ref={(el) => {
                tabRefs.current[i] = el;
              }}
              id={`showcase-tab-${i}`}
              type="button"
              role="tab"
              aria-selected={showcaseStep === i}
              aria-controls={`showcase-panel-${i}`}
              tabIndex={showcaseStep === i ? 0 : -1}
              className={`rail-step ${showcaseStep === i ? "active" : ""} ${showcaseStep > i ? "done" : ""}`}
              onClick={() => selectStep(i)}
              onKeyDown={(e) => onKeyDown(e, i)}
              onFocus={() => setSuspended(true)}
              onBlur={() => setSuspended(false)}
            >
              <span className="rail-num">{i + 1}</span>
              <span className="rail-label">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {showCaption && (
        <p className="showcase-caption">
          A live look at the operating loop — connect, scan, review, export.{" "}
          <Link href="/demo" className="showcase-link">Watch the full walkthrough &rarr;</Link>
        </p>
      )}
    </>
  );
}
