import type { Metadata } from "next";
import ReadinessTool from "./ReadinessTool";

export const metadata: Metadata = {
  title: "DPDP Readiness Score — CompliSense-AI",
  description:
    "Free, no-login self-assessment: answer a short questionnaire and get your DPDP (India) readiness score plus your top gaps. Readiness tooling, not legal advice.",
};

export default function ReadinessPage() {
  return (
    <main className="section" style={{ maxWidth: 820, margin: "0 auto", padding: "3rem 1.25rem" }}>
      <p className="section-kicker">Free tool · no login</p>
      <h1>DPDP Readiness Score</h1>
      <p className="body-text">
        Most early-stage Indian startups have no compliance artefact folder — so we ask instead.
        Answer a few questions and get an honest readiness score for the Digital Personal Data
        Protection Act, framed around the ~May 2027 compliance deadline. We only flag what actually
        applies to you.
      </p>
      <p className="body-text" style={{ fontSize: "0.78rem", opacity: 0.8 }}>
        This is a compliance-<strong>readiness</strong> self-assessment, not legal advice and not a
        determination of compliance. Verify against the primary law and consult a qualified
        practitioner before relying on the results.
      </p>
      <div style={{ marginTop: "2rem" }}>
        <ReadinessTool />
      </div>
    </main>
  );
}
