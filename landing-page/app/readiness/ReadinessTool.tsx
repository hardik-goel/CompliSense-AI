"use client";

import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "https://api.complisenseai.com";
const SIGNUP_URL =
  process.env.NEXT_PUBLIC_APP_BASE_URL || "https://complisense-ai-backend.onrender.com";

type Question = {
  id: string;
  section: string;
  text: string;
  type: "bool" | "single" | "multi" | "number" | "text";
  options?: string[];
  help?: string;
  optional?: boolean;
};

type Gap = {
  rule_id: string;
  title: string;
  severity: string;
  act_citation?: string;
  rule_citation?: string;
  framing: string;
  verification?: string;
};

type ScoreResponse = {
  readiness_score: number | null;
  scoring_available?: boolean;
  obligations_identified?: number;
  jurisdiction?: string;
  summary: { ready: number; gaps: number; applicable: number; not_applicable: number };
  top_gaps?: Gap[];
  gaps_locked?: number;
  disclaimer: string;
  incomplete_questions: string[];
};

const REGULATIONS = [
  { pack_id: "dpdp_india_core_v1", label: "India DPDP" },
  { pack_id: "euai_extended_v1", label: "EU AI Act" },
];

function prettyLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ReadinessTool() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [packId, setPackId] = useState<string>("dpdp_india_core_v1");

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/readiness/questionnaire`)
      .then((r) => r.json())
      .then((d) => setQuestions(d.questions || []))
      .catch(() => setError("Could not load the questionnaire. Please try again later."))
      .finally(() => setLoading(false));
  }, []);

  function setAnswer(id: string, value: unknown) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }

  function toggleMulti(id: string, option: string) {
    setAnswers((prev) => {
      const current = Array.isArray(prev[id]) ? (prev[id] as string[]) : [];
      const next = current.includes(option)
        ? current.filter((o) => o !== option)
        : [...current, option];
      return { ...prev, [id]: next };
    });
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/readiness/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers, pack_id: packId }),
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      setResult(await res.json());
    } catch {
      setError("Could not score your answers. Please try again later.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="body-text">Loading questionnaire…</p>;
  if (error && !result) return <p className="body-text">{error}</p>;

  if (result) {
    return (
      <div className="readiness-result">
        <div className="panel" style={{ textAlign: "center", padding: "2rem" }}>
          {result.scoring_available === false ? (
            <>
              <p className="section-kicker">
                {result.jurisdiction === "EU_AI_ACT" ? "EU AI Act readiness" : "Readiness"}
              </p>
              <div style={{ fontSize: "2rem", fontWeight: 700 }}>Under assessment</div>
              <p className="body-text">
                {result.obligations_identified ?? result.summary.applicable} applicable obligation(s)
                identified · {result.summary.not_applicable} not applicable to you. EU posture scoring
                is pending professional legal review, so no numeric score is shown — review the
                obligations below.
              </p>
            </>
          ) : (
            <>
              <p className="section-kicker">Your DPDP Readiness Score</p>
              <div style={{ fontSize: "3.5rem", fontWeight: 700 }}>{result.readiness_score}%</div>
              <p className="body-text">
                {result.summary.ready} ready · {result.summary.gaps} gaps ·{" "}
                {result.summary.not_applicable} not applicable to you
              </p>
            </>
          )}
        </div>

        <h3 style={{ marginTop: "1.5rem" }}>
          {result.scoring_available === false ? "Obligations to prepare for" : "Top gaps to address"}
        </h3>
        {(result.top_gaps || []).map((g) => (
          <div key={g.rule_id} className="security-item" data-animate style={{ marginBottom: "0.75rem" }}>
            <strong className="author-name">
              {g.title} <span style={{ fontSize: "0.7rem", opacity: 0.7 }}>({g.severity})</span>
            </strong>
            <p className="body-text" style={{ fontSize: "0.82rem" }}>
              {g.act_citation || g.rule_citation} — {g.framing}
            </p>
            {g.verification && g.verification !== "primary_source_verified" ? (
              <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.75 }}>
                ⚠ Source: {g.verification.replace(/_/g, " ")} — not yet primary-verified; treat as indicative.
              </p>
            ) : null}
          </div>
        ))}

        {result.gaps_locked && result.gaps_locked > 0 ? (
          <div className="panel" style={{ padding: "1.25rem", textAlign: "center" }}>
            <p className="body-text">
              <strong>{result.gaps_locked} more gaps</strong> plus tailored remediation steps are in
              your full report.
            </p>
            <a className="btn-primary" href={`${SIGNUP_URL}/register`}>
              Sign up to unlock the full report
            </a>
          </div>
        ) : null}

        <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.75, marginTop: "1.5rem" }}>
          {result.disclaimer}
        </p>
        <button className="btn-secondary" style={{ marginTop: "1rem" }} onClick={() => setResult(null)}>
          Start over
        </button>
      </div>
    );
  }

  // Group questions by section for rendering.
  const sections = questions.reduce<Record<string, Question[]>>((acc, q) => {
    (acc[q.section] = acc[q.section] || []).push(q);
    return acc;
  }, {});

  return (
    <div className="readiness-form">
      <fieldset style={{ border: "none", marginBottom: "1.5rem" }}>
        <legend className="section-kicker">Regulation</legend>
        <div className="field field-full">
          <label htmlFor="regulation">Which regulation do you want a readiness check for?</label>
          <select id="regulation" value={packId} onChange={(e) => setPackId(e.target.value)}>
            {REGULATIONS.map((r) => (
              <option key={r.pack_id} value={r.pack_id}>{r.label}</option>
            ))}
          </select>
          <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.7, margin: "0.2rem 0" }}>
            DPDP returns a readiness score. EU AI Act returns the applicable obligations (no numeric
            score yet — EU posture scoring is pending legal review). Answer the "EU AI Act (if
            applicable)" questions for an EU check.
          </p>
        </div>
      </fieldset>
      {Object.entries(sections).map(([section, qs]) => (
        <fieldset key={section} style={{ border: "none", marginBottom: "1.5rem" }}>
          <legend className="section-kicker">{section}</legend>
          {qs.map((q) => (
            <div className="field field-full" key={q.id} style={{ marginBottom: "1rem" }}>
              <label htmlFor={q.id}>
                {q.text}
                {q.optional ? " (optional)" : ""}
              </label>
              {q.help ? (
                <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.7, margin: "0.2rem 0" }}>
                  {q.help}
                </p>
              ) : null}

              {q.type === "bool" && (
                <div>
                  {["yes", "no"].map((opt) => (
                    <label key={opt} style={{ marginRight: "1rem", fontWeight: 400 }}>
                      <input
                        type="radio"
                        name={q.id}
                        checked={answers[q.id] === (opt === "yes")}
                        onChange={() => setAnswer(q.id, opt === "yes")}
                      />{" "}
                      {prettyLabel(opt)}
                    </label>
                  ))}
                </div>
              )}

              {q.type === "single" && (
                <select
                  id={q.id}
                  value={(answers[q.id] as string) || ""}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                >
                  <option value="" disabled>
                    Select…
                  </option>
                  {(q.options || []).map((opt) => (
                    <option key={opt} value={opt}>
                      {prettyLabel(opt)}
                    </option>
                  ))}
                </select>
              )}

              {q.type === "multi" && (
                <div>
                  {(q.options || []).map((opt) => (
                    <label key={opt} style={{ marginRight: "1rem", fontWeight: 400, display: "inline-block" }}>
                      <input
                        type="checkbox"
                        checked={Array.isArray(answers[q.id]) && (answers[q.id] as string[]).includes(opt)}
                        onChange={() => toggleMulti(q.id, opt)}
                      />{" "}
                      {prettyLabel(opt)}
                    </label>
                  ))}
                </div>
              )}

              {q.type === "number" && (
                <input
                  id={q.id}
                  type="number"
                  min={0}
                  value={(answers[q.id] as number) ?? ""}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                />
              )}

              {q.type === "text" && (
                <input
                  id={q.id}
                  type="text"
                  value={(answers[q.id] as string) || ""}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                />
              )}
            </div>
          ))}
        </fieldset>
      ))}

      {error ? <p className="body-text">{error}</p> : null}

      <button className="btn-primary" onClick={handleSubmit} disabled={submitting}>
        {submitting ? "Scoring…" : "Get my DPDP Readiness Score"}
      </button>
      <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.7, marginTop: "0.75rem" }}>
        Your answers are processed to generate your score and are <strong>not stored</strong> for
        anonymous visitors. This is a readiness self-assessment, not legal advice.
      </p>
    </div>
  );
}
