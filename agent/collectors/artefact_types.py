"""Artefact types the collector recognises (self-contained so it ships in the agent bundle).

Each type carries keywords + filename stems that drive the deterministic classifier and guide
the LLM prompt. Ids align with the hosted artefact generator where they overlap.
"""

from __future__ import annotations

from typing import Any, Dict, List

ARTEFACT_TYPES: List[Dict[str, Any]] = [
    {"id": "privacy_notice", "title": "Privacy notice / policy",
     "filenames": ["privacy_notice", "privacy_policy", "privacy"],
     "keywords": ["privacy notice", "privacy policy", "personal data", "data principal", "purpose of processing"]},
    {"id": "consent_policy", "title": "Consent & withdrawal policy",
     "filenames": ["consent", "consent_policy"],
     "keywords": ["consent", "withdraw consent", "opt-in", "consent manager"]},
    {"id": "security_safeguards", "title": "Security safeguards",
     "filenames": ["security", "security_policy", "safeguards", "infosec"],
     "keywords": ["encryption", "access control", "security safeguard", "least privilege", "at rest", "in transit"]},
    {"id": "breach_process", "title": "Breach response process",
     "filenames": ["breach", "incident", "incident_response"],
     "keywords": ["data breach", "incident response", "notify", "breach register", "containment"]},
    {"id": "retention_schedule", "title": "Retention & erasure schedule",
     "filenames": ["retention", "retention_schedule", "erasure", "deletion"],
     "keywords": ["retention period", "erasure", "deletion", "retain", "disposal"]},
    {"id": "grievance_redressal", "title": "Grievance redressal",
     "filenames": ["grievance", "redressal", "complaints", "dpo"],
     "keywords": ["grievance", "redressal", "complaint", "data protection officer", "contact us"]},
    {"id": "processor_inventory", "title": "Processor / vendor inventory",
     "filenames": ["processor", "vendor", "subprocessors", "dpa"],
     "keywords": ["processor", "sub-processor", "vendor", "data processing agreement", "third party"]},
    {"id": "technical_documentation", "title": "AI technical documentation / model card",
     "filenames": ["model_card", "modelcard", "technical_documentation", "system_card"],
     "keywords": ["model card", "training data", "intended use", "evaluation", "architecture", "limitations"]},
    {"id": "risk_management", "title": "AI risk-management",
     "filenames": ["risk", "risk_management", "risk_assessment"],
     "keywords": ["risk management", "risk assessment", "mitigation", "residual risk", "foreseeable misuse"]},
    {"id": "human_oversight", "title": "Human-oversight measures",
     "filenames": ["human_oversight", "oversight", "hitl"],
     "keywords": ["human oversight", "human-in-the-loop", "human review", "override", "stop button"]},
    {"id": "record_of_processing", "title": "Record of processing / data-flow",
     "filenames": ["ropa", "record_of_processing", "data_flow", "dataflow", "data_inventory"],
     "keywords": ["record of processing", "data flow", "categories of data", "cross-border", "data inventory"]},
]

# id -> title lookup
TITLES: Dict[str, str] = {t["id"]: t["title"] for t in ARTEFACT_TYPES}
