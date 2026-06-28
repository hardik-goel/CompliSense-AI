"""Classify a candidate file into an artefact type.

Primary path is an LLM (Claude) that reads a content sample locally — contents never leave the
machine; the user's own ANTHROPIC_API_KEY calls Anthropic directly. Falls back to a deterministic
filename + keyword classifier when there is no key or the LLM errors/declines, so the collector
always works offline. The LLM client is injectable for tests.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from agent.collectors.artefact_types import ARTEFACT_TYPES, TITLES


@dataclass
class Classification:
    artefact_id: Optional[str]
    confidence: float
    reason: str
    method: str  # "llm" | "deterministic"


def deterministic_classify(filename: str, sample: str) -> Classification:
    """Score each type by filename-stem + keyword hits. Cheap, offline, predictable."""
    name = filename.lower()
    text = (sample or "").lower()
    best_id, best_score, best_reason = None, 0.0, ""
    for t in ARTEFACT_TYPES:
        score = 0.0
        for stem in t["filenames"]:
            if stem in name:
                score += 2.0
        hits = [k for k in t["keywords"] if k in text]
        score += len(hits)
        if score > best_score:
            best_id, best_score, best_reason = t["id"], score, (
                f"filename/keyword match ({', '.join(hits[:3]) or 'name'})")
    if not best_id or best_score < 1.0:
        return Classification(None, 0.0, "no filename/keyword match", "deterministic")
    # squash score into a 0.5–0.95 confidence band
    confidence = min(0.95, 0.5 + 0.12 * best_score)
    return Classification(best_id, round(confidence, 2), best_reason, "deterministic")


class AnthropicClassifier:
    """LLM classifier — lazy Anthropic SDK, model claude-opus-4-8, handles refusal."""

    def __init__(self, model: str = "claude-opus-4-8", api_key: Optional[str] = None):
        self.model = model
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def available(self) -> bool:
        return bool(self._api_key)

    def classify(self, filename: str, sample: str) -> Classification:
        import anthropic  # lazy

        catalog = "\n".join(f"- {t['id']}: {t['title']}" for t in ARTEFACT_TYPES)
        prompt = (
            "You classify a document into ONE compliance-artefact type, or 'none' if it is not a "
            "compliance artefact. Reply with JSON only: "
            '{"artefact_id": "<id-or-none>", "confidence": <0..1>, "reason": "<short>"}.\n\n'
            f"Types:\n{catalog}\n\n"
            f"Filename: {filename}\n"
            f"Content sample (truncated):\n{sample[:3000]}\n"
        )
        client = anthropic.Anthropic(api_key=self._api_key)
        resp = client.messages.create(
            model=self.model, max_tokens=400,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        if getattr(resp, "stop_reason", None) == "refusal":
            return deterministic_classify(filename, sample)
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
        return _parse_llm(text, filename, sample)


def _parse_llm(text: str, filename: str, sample: str) -> Classification:
    try:
        start, end = text.find("{"), text.rfind("}")
        data: dict[str, Any] = json.loads(text[start:end + 1])
        aid = data.get("artefact_id")
        if aid in (None, "none", "") or aid not in TITLES:
            return Classification(None, float(data.get("confidence", 0.0)),
                                  data.get("reason", "not a recognised artefact"), "llm")
        return Classification(aid, float(data.get("confidence", 0.7)),
                              data.get("reason", "llm classification"), "llm")
    except Exception:
        # LLM gave unparseable output — fall back rather than crash.
        return deterministic_classify(filename, sample)


def classify(filename: str, sample: str, llm: Optional[Any] = None) -> Classification:
    """Classify with the LLM when available, else deterministically. Never raises."""
    if llm is not None:
        try:
            if hasattr(llm, "available") and not llm.available():
                return deterministic_classify(filename, sample)
            return llm.classify(filename, sample)
        except Exception:
            return deterministic_classify(filename, sample)
    return deterministic_classify(filename, sample)
