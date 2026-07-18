from __future__ import annotations

from dataclasses import asdict, dataclass
import os


@dataclass(frozen=True)
class RulepackDefinition:
    pack_id: str
    label: str
    regulation: str
    jurisdiction: str
    market: str
    version: str
    description: str
    default_project_standard: str
    sample_artifact_root: str


RULEPACKS: tuple[RulepackDefinition, ...] = (
    RulepackDefinition(
        pack_id="euai_core_v1",
        label="EU AI Act Core v1.0",
        regulation="EU AI Act",
        jurisdiction="EU_AI_ACT",
        market="European Union",
        version="1.0.0",
        description="Starter pack for high-level AI governance and documentation checks under the EU AI Act.",
        default_project_standard="EU_AI_ACT",
        sample_artifact_root="artefacts",
    ),
    RulepackDefinition(
        pack_id="euai_extended_v1",
        label="EU AI Act Extended v1.0",
        regulation="EU AI Act",
        jurisdiction="EU_AI_ACT",
        market="European Union",
        version="1.0.0",
        description="Extended EU AI Act pack with broader governance and monitoring checks.",
        default_project_standard="EU_AI_ACT",
        sample_artifact_root="artefacts",
    ),
    # v2 packs — Digital Omnibus on AI (final, in force Jul 2026). v1 kept registered above
    # for report reproducibility; v2 carries the confirmed dates + new Omnibus rules.
    RulepackDefinition(
        pack_id="euai_core_v2",
        label="EU AI Act Core v2.0 (Digital Omnibus)",
        regulation="EU AI Act",
        jurisdiction="EU_AI_ACT",
        market="European Union",
        version="2.0.0",
        description="EU AI Act core pack updated for the final Digital Omnibus on AI (confirmed high-risk dates).",
        default_project_standard="EU_AI_ACT",
        sample_artifact_root="artefacts",
    ),
    RulepackDefinition(
        pack_id="euai_extended_v2",
        label="EU AI Act Extended v2.0 (Digital Omnibus)",
        regulation="EU AI Act",
        jurisdiction="EU_AI_ACT",
        market="European Union",
        version="2.0.0",
        description="Extended EU AI Act pack updated for the Digital Omnibus: confirmed dates, NCII/CSAM prohibition, deployer/authrep/FRIA/incident duties.",
        default_project_standard="EU_AI_ACT",
        sample_artifact_root="artefacts",
    ),
    RulepackDefinition(
        pack_id="dpdp_india_core_v1",
        label="DPDP India Core v1.0",
        regulation="Digital Personal Data Protection Act, 2023",
        jurisdiction="DPDP_INDIA",
        market="India",
        version="1.0.0",
        description="Starter pack for Digital Personal Data Protection Act obligations around notice, consent, safeguards, grievance handling, and significant fiduciary controls.",
        default_project_standard="DPDP_INDIA",
        sample_artifact_root="sample_artefacts/dpdp_india",
    ),
    RulepackDefinition(
        pack_id="dpdp_india_extended_v1",
        label="DPDP India Extended v1.0",
        regulation="Digital Personal Data Protection Act, 2023",
        jurisdiction="DPDP_INDIA",
        market="India",
        version="1.0.0",
        description="Extended DPDP pack with rights handling, retention, legitimate use, processor governance, and cross-border transfer controls.",
        default_project_standard="DPDP_INDIA",
        sample_artifact_root="sample_artefacts/dpdp_india",
    ),
    RulepackDefinition(
        pack_id="dpdp_india_extended_v2",
        label="DPDP India Extended v2.0",
        regulation="Digital Personal Data Protection Act, 2023",
        jurisdiction="DPDP_INDIA",
        market="India",
        version="2.0.0",
        description="Extended DPDP pack adding the right to nominate (s.14) and lawful-guardian consent for persons with disabilities (s.9 proviso). v1 kept for reproducibility.",
        default_project_standard="DPDP_INDIA",
        sample_artifact_root="sample_artefacts/dpdp_india",
    ),
)

_RULEPACK_ID_SET = {rulepack.pack_id for rulepack in RULEPACKS}
DEFAULT_RULEPACK_ID = os.getenv("DEFAULT_RULEPACK_ID", RULEPACKS[0].pack_id)
if DEFAULT_RULEPACK_ID not in _RULEPACK_ID_SET:
    DEFAULT_RULEPACK_ID = RULEPACKS[0].pack_id


def get_rulepack(pack_id: str | None = None) -> RulepackDefinition:
    target = pack_id or DEFAULT_RULEPACK_ID
    for definition in RULEPACKS:
        if definition.pack_id == target:
            return definition
    raise KeyError(f"Unknown rulepack: {target}")


def get_rulepack_catalog() -> list[dict[str, str]]:
    catalog = []
    for rulepack in RULEPACKS:
        payload = asdict(rulepack)
        payload["is_default"] = rulepack.pack_id == DEFAULT_RULEPACK_ID
        catalog.append(payload)
    return catalog


def get_rulepack_ids() -> list[str]:
    return [rulepack.pack_id for rulepack in RULEPACKS]


def get_rulepack_display_label(pack_id: str | None) -> str:
    """
    Return human-readable labels used in reports for both v1 and non-v1 IDs.
    """
    if not pack_id:
        return "Unknown Rulepack"

    key = pack_id.strip().lower()
    mapping = {
        "dpdp_india_core": "DPDP-Core",
        "dpdp_india_core_v1": "DPDP-Core",
        "dpdp_india_extended": "DPDP-Extended",
        "dpdp_india_extended_v1": "DPDP-Extended",
        "euai_core": "EU-AI Core",
        "euai_core_v1": "EU-AI Core",
        "euai_core_v2": "EU-AI Core v2",
        "euai_extended": "EU-AI Extended",
        "euai_extended_v1": "EU-AI Extended",
        "euai_extended_v2": "EU-AI Extended v2",
        "dpdp_india_extended_v2": "DPDP-Extended v2",
    }
    return mapping.get(key, pack_id)
