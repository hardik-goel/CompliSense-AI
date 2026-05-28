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
