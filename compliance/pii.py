"""Tier-2 PII inference from field/element NAMES (Phase 4.1).

Phase 1 asks the founder to self-declare which personal-data categories they collect.
This module corroborates that by inferring categories from the *names* of their data
elements — column names, JSON keys, form fields — never the values.

Privacy stance (non-negotiable): inference runs on NAMES ONLY. We never read, store, or
reason over actual personal-data values, so "we don't store your source artefacts /
personal data" holds. The only evidence surfaced is the matched field name.

Output is a set of *suggestions* mapped to the manifest's ``pii_categories`` field — a
human reviews and confirms. Nothing is auto-applied. Readiness framing, not legal advice.

Pure logic, no I/O — runs in the hosted API and (later) the local agent.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

# category -> list of (keyword, confidence). Keywords are matched case-insensitively against
# tokenised field names. Short keywords (<=3 chars) match only as an exact token to avoid
# false positives (e.g. "pan" must not fire on "company"); longer ones match as substrings.
PII_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    "email": [("email", "high"), ("e_mail", "high"), ("mail", "medium")],
    "phone": [("phone", "high"), ("mobile", "high"), ("msisdn", "high"), ("tel", "medium"),
              ("contact_number", "high"), ("contactnumber", "high"), ("whatsapp", "medium")],
    "name": [("first_name", "high"), ("last_name", "high"), ("full_name", "high"),
             ("firstname", "high"), ("lastname", "high"), ("surname", "high"),
             ("fname", "medium"), ("lname", "medium"), ("name", "low")],
    "financial": [("credit_card", "high"), ("creditcard", "high"), ("debit", "high"),
                  ("card_number", "high"), ("cardnumber", "high"), ("iban", "high"),
                  ("cvv", "high"), ("upi", "high"), ("ifsc", "high"), ("bank", "medium"),
                  ("account_number", "medium"), ("salary", "medium")],
    "health": [("health", "high"), ("diagnosis", "high"), ("medical", "high"),
               ("blood_group", "high"), ("bloodgroup", "high"), ("prescription", "high"),
               ("disease", "high"), ("patient", "medium")],
    "biometric": [("biometric", "high"), ("fingerprint", "high"), ("faceprint", "high"),
                  ("face_embedding", "high"), ("face_id", "high"), ("iris", "high"), ("retina", "high")],
    "location": [("latitude", "high"), ("longitude", "high"), ("location", "high"), ("gps", "high"),
                 ("lat", "medium"), ("lon", "medium"), ("lng", "medium"), ("geo", "medium"),
                 ("address", "medium"), ("pincode", "medium"), ("zipcode", "medium"), ("postal", "medium")],
    "government_id": [("aadhaar", "high"), ("aadhar", "high"), ("uidai", "high"), ("pan", "high"),
                      ("ssn", "high"), ("passport", "high"), ("voter_id", "high"),
                      ("driving_license", "high"), ("driving_licence", "high"),
                      ("national_id", "high"), ("nationalid", "high"), ("tax_id", "medium")],
    "children_data": [("child", "high"), ("minor", "medium"), ("guardian", "high"),
                      ("parent_consent", "high"), ("parentconsent", "high"), ("is_minor", "high")],
}

_CONF_RANK = {"high": 2, "medium": 1, "low": 0}


@dataclass
class PIIFinding:
    category: str
    matched_on: List[str]
    confidence: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PIISuggestion:
    """Mirror of the connector Suggestion shape, kept local so compliance/ stays standalone."""
    manifest_field: str
    suggested_value: Any
    confidence: str
    rationale: str
    action: str = "review"
    evidence_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _tokenize(name: str) -> Tuple[str, set]:
    """Return (normalized_joined, token_set) for a field name.

    Splits camelCase and any non-alphanumeric boundary: ``userEmailID`` -> tokens
    {user, email, id} and joined ``user email id``.
    """
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name or "")
    parts = re.split(r"[^a-zA-Z0-9]+", spaced.lower())
    tokens = {p for p in parts if p}
    return " ".join(p for p in parts if p), tokens


def _matches(keyword: str, joined: str, tokens: set) -> bool:
    if len(keyword) <= 3:
        return keyword in tokens  # exact token only — avoids "pan" in "company"
    kw = keyword.replace("_", " ")
    return kw in joined or keyword in tokens


def infer_pii(field_names: List[str]) -> List[PIIFinding]:
    """Infer PII categories from a list of field/column/element names (names only)."""
    # category -> {confidence_rank, matched_on:set}
    hits: Dict[str, Dict[str, Any]] = {}
    for raw in field_names or []:
        if not isinstance(raw, str) or not raw.strip():
            continue
        joined, tokens = _tokenize(raw)
        for category, patterns in PII_PATTERNS.items():
            best = None
            for keyword, conf in patterns:
                if _matches(keyword, joined, tokens):
                    if best is None or _CONF_RANK[conf] > _CONF_RANK[best]:
                        best = conf
            if best is not None:
                bucket = hits.setdefault(category, {"rank": -1, "conf": "low", "matched_on": set()})
                bucket["matched_on"].add(raw)
                if _CONF_RANK[best] > bucket["rank"]:
                    bucket["rank"] = _CONF_RANK[best]
                    bucket["conf"] = best

    findings = [
        PIIFinding(category=cat, matched_on=sorted(b["matched_on"]), confidence=b["conf"])
        for cat, b in hits.items()
    ]
    findings.sort(key=lambda f: (-_CONF_RANK[f.confidence], f.category))
    return findings


def pii_to_suggestion(findings: List[PIIFinding]) -> PIISuggestion | None:
    """Collapse findings into one ``pii_categories`` manifest suggestion (human-confirms)."""
    if not findings:
        return None
    categories = sorted({f.category for f in findings})
    overall = "high" if any(f.confidence == "high" for f in findings) else (
        "medium" if any(f.confidence == "medium" for f in findings) else "low")
    detail = "; ".join(f"{f.category} (from {', '.join(f.matched_on)})" for f in findings)
    evidence = sorted({name for f in findings for name in f.matched_on})
    return PIISuggestion(
        manifest_field="pii_categories",
        suggested_value=categories,
        confidence=overall,
        rationale=f"Field names suggest these personal-data categories — confirm against reality: {detail}.",
        action="review",
        evidence_signals=evidence,
    )
