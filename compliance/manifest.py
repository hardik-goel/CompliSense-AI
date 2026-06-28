"""
Tier-0 Guided Manifest — DPDP (Phase 1.1).

Removes the "no artefact folder" blocker: instead of scanning files, we ask the founder a
short, structured questionnaire and build a `compliance.yaml`-equivalent **manifest**. The
manifest does two jobs:

1. **Applicability facts** — entity type, registered-user counts, SDF status, children's
   data, sector, state instrumentality, consent-manager role — feed the Phase-0
   applicability gate (`compliance/applicability.py`) so we never flag a non-SDF startup
   for SDF-only duties.
2. **Processing facts** — what PII is collected, where it is stored, processors, consent
   mechanism, retention, breach/grievance posture — feed the readiness scoring (Phase 1.2).

Grounding: questions and their rule mapping trace to `docs/LEGAL_REFERENCE_DPDP_EUAI.md`
and `docs/SOURCES.md`. This is engineering tooling, not legal advice.

No persistence here — this module is pure data + logic so it runs both in the hosted API
and (later) the local agent. Storage decisions live in the API layer (Phase 1.5).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# Third-Schedule registered-user triggers (DPDP Rules 2025, Rule 8(1) + Third Schedule).
THIRD_SCHEDULE_TRIGGERS = {
    "ecommerce": 20_000_000,      # >= 2 crore registered users
    "social_media": 20_000_000,   # >= 2 crore registered users
    "online_gaming": 5_000_000,   # >= 50 lakh registered users
}


# ── Questionnaire definition ─────────────────────────────────────────────────
# Each question declares: id, text, type, options (for single/multi), and `maps_to`
# describing how the answer flows into the manifest. Kept declarative so the API and the
# web UI render from the same source of truth.

QUESTIONS: List[Dict[str, Any]] = [
    # --- Applicability facts ---
    {
        "id": "entity_type",
        "section": "About your organisation",
        "text": "What best describes your organisation?",
        "type": "single",
        "options": ["individual", "startup", "enterprise", "government_body", "other"],
        "help": "Determines baseline Data Fiduciary status.",
    },
    {
        "id": "offers_in_india",
        "section": "About your organisation",
        "text": "Do you offer goods or services to individuals in India (or process their data)?",
        "type": "bool",
        "help": "DPDP applies within India and extraterritorially to those serving Indian users (Act s.3).",
    },
    {
        "id": "sector",
        "section": "About your organisation",
        "text": "Which sector best fits your product?",
        "type": "single",
        "options": ["ecommerce", "social_media", "online_gaming", "healthcare",
                    "edtech", "fintech", "saas", "other"],
        "help": "Some sectors carry extra obligations or exemptions.",
    },
    {
        "id": "registered_users",
        "section": "About your organisation",
        "text": "Roughly how many registered users do you have in India?",
        "type": "number",
        "help": "Used only to check Third-Schedule class triggers (e-commerce/social >=2cr, gaming >=50L).",
    },
    {
        "id": "notified_as_sdf",
        "section": "About your organisation",
        "text": "Has the Central Government notified you as a Significant Data Fiduciary (SDF)?",
        "type": "bool",
        "help": "SDF duties (DPIA, audit, India DPO) apply ONLY to notified SDFs. Most startups are NOT SDFs.",
    },
    {
        "id": "is_state_instrumentality",
        "section": "About your organisation",
        "text": "Are you a State or an instrumentality of the State?",
        "type": "bool",
        "help": "Certain State processing follows the Second Schedule standards (Rule 5).",
    },
    {
        "id": "acts_as_consent_manager",
        "section": "About your organisation",
        "text": "Do you operate as a registered Consent Manager?",
        "type": "bool",
        "help": "Consent Manager obligations (Rule 4) apply only if you act as one.",
    },
    {
        "id": "processes_children_data",
        "section": "Data you handle",
        "text": "Do you knowingly process personal data of children (under 18)?",
        "type": "bool",
        "help": "Triggers verifiable parental consent (Rule 10) + Act s.9 bans, subject to Fourth-Schedule exemptions.",
    },
    {
        "id": "cross_border_transfer",
        "section": "Data you handle",
        "text": "Do you transfer personal data outside India?",
        "type": "bool",
        "help": "Permitted subject to future Central-Govt restrictions (Rule 15).",
    },
    # --- Processing facts (readiness) ---
    {
        "id": "pii_categories",
        "section": "Data you handle",
        "text": "Which categories of personal data do you collect?",
        "type": "multi",
        "options": ["name", "email", "phone", "financial", "health", "biometric",
                    "location", "government_id", "children_data", "none"],
        "help": "Itemised personal data must be listed in your notice (Rule 3).",
    },
    {
        "id": "storage_locations",
        "section": "Data you handle",
        "text": "Where does that data live?",
        "type": "multi",
        "options": ["aws", "gcp", "azure", "render", "on_prem", "third_party_saas", "notebooks", "unsure"],
        "help": "Used to map where personal data may reside (informs security & processor checks).",
    },
    {
        "id": "has_privacy_notice",
        "section": "Your current posture",
        "text": "Do you have a standalone, plain-language privacy notice?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC5-NOTICE-001",
    },
    {
        "id": "consent_mechanism",
        "section": "Your current posture",
        "text": "How do you obtain consent?",
        "type": "single",
        "options": ["explicit_optin", "pre_ticked_or_implied", "none"],
        "maps_to_rule": "DPDP-SEC6-CONSENT-001",
    },
    {
        "id": "has_withdrawal_mechanism",
        "section": "Your current posture",
        "text": "Can users withdraw consent as easily as they gave it?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC6-CONSENT-001",
    },
    {
        "id": "has_security_safeguards",
        "section": "Your current posture",
        "text": "Do you have documented security safeguards (encryption, access control, logging)?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC8-OBLIGATIONS-001",
    },
    {
        "id": "has_breach_process",
        "section": "Your current posture",
        "text": "Do you have a personal-data-breach response process / register?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC8-OBLIGATIONS-002",
    },
    {
        "id": "retention_defined",
        "section": "Your current posture",
        "text": "Have you defined data retention and erasure periods?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC8-OBLIGATIONS-003",
    },
    {
        "id": "has_grievance_contact",
        "section": "Your current posture",
        "text": "Do you publish a grievance/contact point for data questions?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC13-GRIEVANCE-001",
    },
    {
        "id": "grievance_email",
        "section": "Your current posture",
        "text": "What is the published grievance contact email? (optional)",
        "type": "text",
        "optional": True,
    },
    {
        "id": "processors_listed",
        "section": "Your current posture",
        "text": "Do you maintain an inventory of processors/vendors with data-processing contracts?",
        "type": "bool",
        "maps_to_rule": "DPDP-SEC8-PROCESSOR-001",
    },
    # --- EU AI Act facts (applicability only; EU posture scoring pending legal review) ---
    {
        "id": "has_ai_system",
        "section": "EU AI Act (if applicable)",
        "text": "Do you build, deploy, import, or distribute an AI system?",
        "type": "bool",
        "help": "Gates whether EU AI Act obligations apply at all.",
        "optional": True,
    },
    {
        "id": "eu_role",
        "section": "EU AI Act (if applicable)",
        "text": "What is your role for that AI system?",
        "type": "single",
        "options": ["none", "provider", "deployer", "importer", "distributor",
                    "gpai_provider", "gpai_downstream"],
        "help": "EU AI Act obligations are role-gated (provider duties differ from deployer duties).",
        "optional": True,
    },
    {
        "id": "provides_to_eu",
        "section": "EU AI Act (if applicable)",
        "text": "Is the AI system placed on the EU market or is its output used in the EU?",
        "type": "bool",
        "help": "The EU AI Act applies extraterritorially when output is used in the EU (Art. 2).",
        "optional": True,
    },
    {
        "id": "is_open_source",
        "section": "EU AI Act (if applicable)",
        "text": "Is the AI model/system released under a free and open-source licence?",
        "type": "bool",
        "help": "Some EU AI Act duties carry open-source carve-outs (scope subject to legal review).",
        "optional": True,
    },
]

QUESTION_IDS = {q["id"] for q in QUESTIONS}


@dataclass
class Manifest:
    """A compliance.yaml-equivalent manifest built from questionnaire answers."""

    # Applicability facts
    entity_type: str = "startup"
    offers_in_india: bool = True
    sector: str = "other"
    registered_users: int = 0
    notified_as_sdf: bool = False
    is_state_instrumentality: bool = False
    acts_as_consent_manager: bool = False
    processes_children_data: bool = False
    cross_border_transfer: bool = False
    # Processing facts
    pii_categories: List[str] = field(default_factory=list)
    storage_locations: List[str] = field(default_factory=list)
    has_privacy_notice: bool = False
    consent_mechanism: str = "none"
    has_withdrawal_mechanism: bool = False
    has_security_safeguards: bool = False
    has_breach_process: bool = False
    retention_defined: bool = False
    has_grievance_contact: bool = False
    grievance_email: Optional[str] = None
    processors_listed: bool = False
    # EU AI Act facts
    has_ai_system: bool = False
    eu_role: str = "none"
    provides_to_eu: bool = False
    is_open_source: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _coerce_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y", "on")
    return bool(v)


def build_manifest(answers: Dict[str, Any]) -> Manifest:
    """Build a Manifest from a questionnaire answer dict (extra/missing keys tolerated)."""
    m = Manifest()
    type_by_id = {q["id"]: q["type"] for q in QUESTIONS}
    for key, val in (answers or {}).items():
        if key not in QUESTION_IDS or not hasattr(m, key):
            continue
        qtype = type_by_id.get(key)
        if qtype == "bool":
            setattr(m, key, _coerce_bool(val))
        elif qtype == "number":
            try:
                setattr(m, key, int(val))
            except (TypeError, ValueError):
                setattr(m, key, 0)
        elif qtype == "multi":
            setattr(m, key, list(val) if isinstance(val, (list, tuple)) else [val])
        else:  # single / text
            setattr(m, key, val)
    return m


def is_third_schedule_class(manifest: Manifest) -> bool:
    """True if the entity falls in a Third-Schedule class by sector + registered-user count."""
    trigger = THIRD_SCHEDULE_TRIGGERS.get(manifest.sector)
    return bool(trigger and manifest.registered_users >= trigger)


# Manifest eu_role value -> applicability scope name.
_EU_ROLE_TO_SCOPE = {
    "provider": "eu_provider",
    "deployer": "eu_deployer",
    "importer": "eu_importer",
    "distributor": "eu_distributor",
    "gpai_provider": "eu_gpai_provider",
    "gpai_downstream": "eu_gpai_downstream",
}


def eu_roles(manifest: Manifest) -> List[str]:
    """Applicability role-scopes for the EU AI Act gate.

    Roles apply only when the entity actually has an AI system with an EU nexus (placed on
    the EU market or output used in the EU, Art. 2). Empty otherwise — so non-EU entities are
    never flagged for EU provider/deployer duties.
    """
    if not manifest.has_ai_system or not manifest.provides_to_eu:
        return []
    scope = _EU_ROLE_TO_SCOPE.get(manifest.eu_role)
    return [scope] if scope else []


def manifest_to_profile(manifest: Manifest) -> Dict[str, Any]:
    """Map a manifest to the entity profile consumed by the applicability gate."""
    return {
        "is_significant_data_fiduciary": bool(manifest.notified_as_sdf),
        "processes_children_data": bool(manifest.processes_children_data),
        "is_third_schedule_class": is_third_schedule_class(manifest),
        "is_consent_manager": bool(manifest.acts_as_consent_manager),
        "is_state_instrumentality": bool(manifest.is_state_instrumentality),
        "eu_roles": eu_roles(manifest),
        "is_open_source": bool(manifest.is_open_source),
    }


def validate_answers(answers: Dict[str, Any]) -> List[str]:
    """Return a list of missing REQUIRED question ids (optional questions excluded)."""
    required = {q["id"] for q in QUESTIONS if not q.get("optional")}
    provided = {k for k, v in (answers or {}).items() if v not in (None, "", [])}
    return sorted(required - provided)


def get_questionnaire() -> List[Dict[str, Any]]:
    """Return the questionnaire definition for rendering (API/UI)."""
    return QUESTIONS
