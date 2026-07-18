"use client";

import { useEffect, useRef, useState } from "react";
import questionnaire from "./questionnaire.json";

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
  tier?: "core" | "deep";
};

/**
 * The questionnaire is a fixed set of questions, so it ships in the bundle
 * rather than costing a round-trip to a free-tier Render service that can
 * cold-start for ~30s. Kept in sync with `compliance.manifest.QUESTIONS` by
 * `tests/test_manifest.py::test_static_questionnaire_json_matches_source`;
 * regenerate via `python scripts/export_questionnaire.py`. Scoring still calls
 * the API.
 */
const QUESTIONS = questionnaire.questions as Question[];

/** Show a "still waking up" note rather than letting a slow call look broken. */
const SLOW_SCORE_NOTICE_MS = 3000;

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

/** Sentinel stored when a user picks "Not sure". Non-empty (so it counts as answered),
 *  but recognised by no scoring predicate — the backend treats it as an honest unknown
 *  (which surfaces as a "needs review" gap rather than a fabricated Yes/No). */
const NOT_SURE = "not_sure";

/** EU AI Act questions live in sections prefixed "EU AI Act". Everything else is DPDP.
 *  We show only the questions relevant to the regulation the visitor picked. */
function isEuQuestion(q: Question): boolean {
  return q.section.startsWith("EU AI Act");
}

export default function ReadinessTool() {
  const questions = QUESTIONS;
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);
  const [scoringSlow, setScoringSlow] = useState(false);
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [packId, setPackId] = useState<string>("dpdp_india_core_v1");
  const slowTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Nudge the scoring service awake while the visitor reads the questions, so
  // the cold start overlaps with the time they were going to spend anyway.
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/api/health`, {
      signal: controller.signal,
      mode: "no-cors", // response is unused; this only wakes the instance
    }).catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => () => {
    if (slowTimer.current) clearTimeout(slowTimer.current);
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
    setScoringSlow(false);
    slowTimer.current = setTimeout(() => setScoringSlow(true), SLOW_SCORE_NOTICE_MS);
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
      if (slowTimer.current) clearTimeout(slowTimer.current);
      setScoringSlow(false);
      setSubmitting(false);
    }
  }

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

  // Show only the questions relevant to the chosen regulation: DPDP hides the EU AI Act
  // sections, and the EU AI Act check hides the DPDP-specific ones (and vice versa).
  const isEuPack = packId.startsWith("euai");
  const visibleQuestions = questions.filter((q) =>
    isEuPack ? isEuQuestion(q) : !isEuQuestion(q)
  );
  // CORE = one-screen ~2-minute set; DEEP = optional, behind an expander.
  const coreQuestions = visibleQuestions.filter((q) => q.tier !== "deep");
  const deepQuestions = visibleQuestions.filter((q) => q.tier === "deep");

  function groupBySection(qs: Question[]): [string, Question[]][] {
    const map = qs.reduce<Record<string, Question[]>>((acc, q) => {
      (acc[q.section] = acc[q.section] || []).push(q);
      return acc;
    }, {});
    return Object.entries(map);
  }

  function renderField(q: Question) {
    return (
      <div className="field field-full" key={q.id} style={{ marginBottom: "1rem" }}>
        <label htmlFor={q.id}>
          {q.text}
          {q.optional ? " (optional)" : ""}
        </label>
        {q.help ? (
          <details className="q-help" style={{ margin: "0.2rem 0" }}>
            <summary
              style={{ fontSize: "0.72rem", opacity: 0.75, cursor: "pointer", userSelect: "none" }}
            >
              What does this mean? Where do I find it?
            </summary>
            <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.7, margin: "0.3rem 0 0" }}>
              {q.help}
            </p>
          </details>
        ) : null}

        {q.type === "bool" && (
          <div className="option-group">
            {["yes", "no"].map((opt) => (
              <label key={opt} className="option-chip">
                <input
                  type="radio"
                  name={q.id}
                  checked={answers[q.id] === (opt === "yes")}
                  onChange={() => setAnswer(q.id, opt === "yes")}
                />
                <span>{prettyLabel(opt)}</span>
              </label>
            ))}
            <label className="option-chip">
              <input
                type="radio"
                name={q.id}
                checked={answers[q.id] === NOT_SURE}
                onChange={() => setAnswer(q.id, NOT_SURE)}
              />
              <span>Not sure</span>
            </label>
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
            <option value={NOT_SURE}>Not sure / don&apos;t know</option>
          </select>
        )}

        {q.type === "multi" && (
          <div className="option-group">
            {(q.options || []).map((opt) => (
              <label key={opt} className="option-chip">
                <input
                  type="checkbox"
                  checked={Array.isArray(answers[q.id]) && (answers[q.id] as string[]).includes(opt)}
                  onChange={() => toggleMulti(q.id, opt)}
                />
                <span>{prettyLabel(opt)}</span>
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
    );
  }

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
            score yet — EU posture scoring is pending legal review).
          </p>
        </div>
      </fieldset>

      {/* CORE questions — one screen, ~2 minutes. */}
      {groupBySection(coreQuestions).map(([section, qs]) => (
        <fieldset key={section} style={{ border: "none", marginBottom: "1.5rem" }}>
          <legend className="section-kicker">{section}</legend>
          {qs.map((q) => renderField(q))}
        </fieldset>
      ))}

      {/* DEEP questions — optional, collapsed. For EU this is the EU AI Act block; for DPDP
          it's the extra precision questions. Unanswered deep questions score as unknown = gap. */}
      {deepQuestions.length > 0 && (
        <details className="deep-questions" style={{ marginBottom: "1.5rem" }}>
          <summary className="section-kicker" style={{ cursor: "pointer", userSelect: "none" }}>
            {isEuPack
              ? "EU AI Act questions (answer these for an EU check)"
              : `Add ${deepQuestions.length} more for a deeper, more precise score`}
          </summary>
          <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.7, margin: "0.5rem 0" }}>
            Optional. Leaving these blank is fine — they simply score as “needs review” rather than
            a pass, so answering more sharpens your score.
          </p>
          {groupBySection(deepQuestions).map(([section, qs]) => (
            <fieldset key={section} style={{ border: "none", marginBottom: "1rem" }}>
              <legend className="section-kicker" style={{ fontSize: "0.78rem" }}>{section}</legend>
              {qs.map((q) => renderField(q))}
            </fieldset>
          ))}
        </details>
      )}

      {error ? (
        <p className="form-error" role="alert">
          {error}{" "}
          <button type="button" className="link-button" onClick={handleSubmit}>
            Retry
          </button>
        </p>
      ) : null}

      <button className="btn-primary" onClick={handleSubmit} disabled={submitting}>
        {submitting
          ? "Scoring…"
          : isEuPack
          ? "Check my EU AI Act readiness"
          : "Get my DPDP Readiness Score"}
      </button>

      {submitting && scoringSlow ? (
        <p className="form-notice" role="status">
          Waking up the scoring service — this can take up to 30 seconds on the first
          request of the day. Your answers are safe; hang tight.
        </p>
      ) : null}
      <p className="body-text" style={{ fontSize: "0.72rem", opacity: 0.7, marginTop: "0.75rem" }}>
        Your answers are processed to generate your score and are <strong>not stored</strong> for
        anonymous visitors. This is a readiness self-assessment, not legal advice.
      </p>
    </div>
  );
}
