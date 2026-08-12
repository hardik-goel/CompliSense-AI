"""LLM Remediation Copilot — grounded, read-only guidance (Phase 7).

Given ONE specific readiness gap, the user's own confirmed facts, and the cited rule, the
copilot explains the gap or DRAFTS a remediation document (policy text, process outline,
checklist). It is grounded and bounded:

  - Answers ONLY from the supplied context (the cited rule + the user's stated facts) — never
    open-ended legal generation. If it can't ground an answer, it says so.
  - Readiness framing, never a compliance/legal determination. Not legal advice.
  - Drafting documents is in scope; instructing the user to mutate live systems (IAM, prod
    configs) is NOT — the copilot assists, a human acts.
  - Consent + data path: the API layer sends only structured, non-PII facts (rule text +
    the project's confirmed manifest booleans), never raw artefacts or personal-data values.

The model call is injectable (`llm`), so tests run with no API key and no network. The
default client uses the Anthropic SDK (claude-opus-4-8, adaptive thinking).
"""

from __future__ import annotations

from typing import Any, Callable, Dict

# llm(system, user) -> assistant text.
LLM = Callable[[str, str], str]

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are CompliSense's remediation copilot. You help an engineering team \
understand and close ONE specific regulatory-readiness gap.

STRICT RULES — follow all of them:
- Answer ONLY using the CONTEXT provided below (the cited rule and the user's own stated \
facts). Do not rely on outside knowledge of the law. If the context is insufficient to \
answer, reply exactly: "I can't ground an answer in your data and the cited rule. Provide \
more detail or consult a qualified practitioner." — and stop.
- Use READINESS framing, never a determination of compliance. Never say the user "is \
compliant" or "is non-compliant". Frame everything as "to be ready for <obligation>, ...".
- This is engineering guidance, NOT legal advice. Do not present it as legal advice.
- You MAY draft documents: policy text, a process outline, a checklist, a notice section. \
You MUST NOT instruct the user to mutate their live systems (changing IAM policies, editing \
production configs, running destructive commands). Drafting text is in scope; changing their \
environment is not.
- When you reference the obligation, cite the rule by its citation string.
- Be concise and concrete. Readiness, not alarm."""

DISCLAIMER = ("Grounded engineering guidance, not legal advice and not a determination of "
              "compliance. Verify against primary sources and consult a qualified practitioner.")

# Stamped into every drafted document so a generated artefact can never be mistaken for a
# finished, lawyer-approved one.
DRAFT_MARKER = "DRAFT — REQUIRES LEGAL REVIEW. Not a final or legally-approved document."

_UNGROUNDED_MARKER = "I can't ground an answer in your data"


def build_context_block(rule: Dict[str, Any], facts: Dict[str, Any]) -> str:
    """Render the grounded CONTEXT (cited rule + the user's confirmed facts) as text.

    ``facts`` must already be non-PII (manifest booleans / categories, readiness status) —
    the API layer is responsible for never passing raw artefacts or personal-data values.
    """
    citation = rule.get("rule_citation") or rule.get("act_citation") or rule.get("clause") or "—"
    lines = [
        "CITED RULE",
        f"- id: {rule.get('rule_id') or rule.get('id')}",
        f"- title: {rule.get('title')}",
        f"- citation: {citation}",
    ]
    if rule.get("act_citation") and rule.get("act_citation") != citation:
        lines.append(f"- act citation: {rule.get('act_citation')}")
    if rule.get("framing"):
        lines.append(f"- enforcement framing: {rule.get('framing')}")
    if rule.get("requirement") or rule.get("description"):
        lines.append(f"- requirement: {rule.get('requirement') or rule.get('description')}")

    lines.append("")
    lines.append("THE USER'S CONFIRMED FACTS (non-PII)")
    if facts:
        for key, value in facts.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- (none provided)")
    return "\n".join(lines)


class RemediationCopilot:
    def __init__(self, llm: LLM):
        self._llm = llm

    def _run(self, instruction: str, context_block: str, mode: str) -> Dict[str, Any]:
        user = f"{instruction}\n\n{context_block}"
        try:
            answer = self._llm(SYSTEM_PROMPT, user)
        except _Refusal:
            return {
                "mode": mode, "grounded": False,
                "answer": "The model declined to answer this request.",
                "disclaimer": DISCLAIMER, "model": MODEL,
            }
        grounded = _UNGROUNDED_MARKER not in (answer or "")
        return {"mode": mode, "grounded": grounded, "answer": answer,
                "disclaimer": DISCLAIMER, "model": MODEL}

    def explain(self, rule: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
        """Explain why this gap matters and what readiness looks like, grounded in the rule."""
        ctx = build_context_block(rule, facts)
        instruction = ("Explain, for this gap: (1) what the cited rule asks for, (2) why the "
                       "user's facts leave a readiness gap, (3) concrete steps to become ready. "
                       "Ground every point in the CONTEXT.")
        return self._run(instruction, ctx, "explain")

    def draft(self, rule: Dict[str, Any], facts: Dict[str, Any], artifact_type: str) -> Dict[str, Any]:
        """Draft a remediation document (text only) for this gap.

        The drafted body is stamped with ``DRAFT_MARKER`` so a generated artefact is never
        mistaken for a finished, lawyer-approved document.
        """
        ctx = build_context_block(rule, facts)
        instruction = (f"Draft a '{artifact_type}' that would help close this readiness gap. "
                       f"Begin the document with this exact line on its own: '{DRAFT_MARKER}'. "
                       "Produce document text only — do not instruct the user to change live "
                       "systems. Ground the content in the CONTEXT.")
        result = self._run(instruction, ctx, "draft")
        # Belt-and-suspenders: ensure the marker is present even if the model omitted it.
        answer = result.get("answer") or ""
        if result.get("grounded") and DRAFT_MARKER not in answer:
            result["answer"] = f"{DRAFT_MARKER}\n\n{answer}"
        result["draft_marker"] = DRAFT_MARKER
        return result


class _Refusal(Exception):
    """Raised by the default LLM client when the model returns stop_reason 'refusal'."""


def default_llm(max_tokens: int = 2000) -> LLM:
    """Build the production LLM client (Anthropic SDK, claude-opus-4-8, adaptive thinking).

    Imported lazily so this module (and the tests) never require the `anthropic` package.
    """

    def _call(system: str, user: str) -> str:
        import anthropic  # lazy: optional dependency
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if resp.stop_reason == "refusal":
            raise _Refusal()
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    return _call


def openrouter_llm(max_tokens: int = 2000) -> LLM:
    """LLM client for OpenAI-format gateways (OpenRouter). Raw HTTP; for testing with free credits.

    Uses OPENROUTER_API_KEY (or OPENAI_API_KEY), OPENROUTER_MODEL (default a free model), and
    OPENAI_BASE_URL (default OpenRouter). Production default stays Anthropic.
    """
    import os

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = (os.getenv("OPENAI_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")
    model = os.getenv("OPENROUTER_MODEL") or "nvidia/nemotron-3-super-120b-a12b:free"

    def _call(system: str, user: str) -> str:
        import requests  # lazy
        r = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
            timeout=120,
        )
        body = r.json()
        if "choices" not in body:
            raise RuntimeError(f"LLM gateway error: {body.get('error', body)}")
        return body["choices"][0]["message"]["content"]

    return _call


def default_llm_from_env(max_tokens: int = 2000) -> LLM:
    """Pick the LLM client from env: OpenRouter (OPENROUTER_API_KEY) > Anthropic."""
    import os
    if os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"):
        return openrouter_llm(max_tokens)
    return default_llm(max_tokens)
