import { ArrowRight, Check, X } from "lucide-react";

const before = [
  "Spreadsheets & shared drives",
  "Vendor reviews in email threads",
  "Consultant PDFs that go stale",
  "Evidence rebuilt before each audit",
];

const after = [
  "One workspace for every obligation",
  "Versioned policies & controls",
  "Evidence collected continuously",
  "Always audit-ready, one-click export",
];

/** Founder-story visual: fragmented tooling (left) → one operating system (right). */
export default function ChaosToOrder() {
  return (
    <div className="c2o" data-animate>
      <div className="c2o-side c2o-chaos">
        <span className="c2o-label c2o-label-bad">Before · fragmented</span>
        <ul className="c2o-list">
          {before.map((t) => (
            <li className="c2o-item c2o-item-bad" key={t}>
              <span className="c2o-mark"><X size={12} strokeWidth={3} /></span>
              {t}
            </li>
          ))}
        </ul>
      </div>

      <div className="c2o-arrow" aria-hidden="true">
        <ArrowRight size={26} />
      </div>

      <div className="c2o-side c2o-order">
        <span className="c2o-label c2o-label-good">After · CompliSense-AI</span>
        <ul className="c2o-list">
          {after.map((t) => (
            <li className="c2o-item c2o-item-good" key={t}>
              <span className="c2o-mark c2o-mark-good"><Check size={12} strokeWidth={3} /></span>
              {t}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
