"""Tier-2 data-flow inference (Phase 4.2).

Builds on the PII engine (compliance/pii.py): given a set of data sources — each a named
store with a provider/region and the NAMES of its fields — infer *which personal-data
categories live where*, and flag categories that sit outside India (a cross-border
transfer worth human review).

Same privacy stance as 4.1: NAMES ONLY. We never read values. Output is a data-flow map +
manifest *suggestions* (pii_categories, storage_locations, cross_border_transfer) that a
human reviews and confirms. Pure, local, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from compliance.pii import PIISuggestion, infer_pii, pii_to_suggestion

# Indian cloud regions across providers (provider-agnostic union). A region is treated as
# Indian if it is in this set or literally contains "india".
INDIA_REGIONS = {
    "ap-south-1", "ap-south-2",            # AWS
    "asia-south1", "asia-south2",          # GCP
    "centralindia", "southindia", "westindia", "jioindiacentral", "jioindiawest",  # Azure
}
# Providers that are valid manifest storage_locations options.
_STORAGE_OPTIONS = {"aws", "gcp", "azure", "render", "on_prem", "third_party_saas", "notebooks", "unsure"}


@dataclass
class DataSource:
    name: str
    field_names: List[str] = field(default_factory=list)
    provider: Optional[str] = None   # aws | gcp | azure | render | on_prem | third_party_saas | ...
    region: Optional[str] = None     # e.g. ap-south-1, us-east-1, asia-south1


def is_india_region(region: Optional[str]) -> bool:
    if not region:
        return False
    r = region.replace(" ", "").lower()
    return r in INDIA_REGIONS or "india" in r


def infer_data_flows(sources: List[DataSource]) -> Dict[str, Any]:
    """Map PII categories across data sources and flag cross-border placement."""
    per_source: List[Dict[str, Any]] = []
    category_to_sources: Dict[str, List[str]] = {}
    cross_border: List[Dict[str, Any]] = []
    all_field_names: List[str] = []
    providers: set = set()

    for src in sources or []:
        findings = infer_pii(src.field_names)
        all_field_names.extend(src.field_names or [])
        in_india = is_india_region(src.region)
        if src.provider:
            providers.add(src.provider)

        per_source.append({
            "name": src.name,
            "provider": src.provider,
            "region": src.region,
            "in_india": in_india,
            "categories": [f.to_dict() for f in findings],
        })

        for f in findings:
            category_to_sources.setdefault(f.category, [])
            if src.name not in category_to_sources[f.category]:
                category_to_sources[f.category].append(src.name)
            # PII in a non-Indian region (and region is known) => cross-border review item.
            if src.region and not in_india:
                cross_border.append({
                    "category": f.category, "source": src.name,
                    "provider": src.provider, "region": src.region,
                })

    suggestions: List[PIISuggestion] = []

    pii_sug = pii_to_suggestion(infer_pii(all_field_names))
    if pii_sug:
        suggestions.append(pii_sug)

    # Children's-data is applicability-changing, not just a category: inferring it should
    # propose flipping processes_children_data, which the readiness gate (Phase 3.4) consumes
    # to make children's-data duties (verifiable parental consent, s.9 bans) applicable.
    if "children_data" in category_to_sources:
        suggestions.append(PIISuggestion(
            manifest_field="processes_children_data",
            suggested_value=True,
            confidence="medium",
            rationale="Field names suggest children's personal data — confirm; this triggers "
                      "verifiable parental-consent and related duties.",
            action="review",
            evidence_signals=category_to_sources.get("children_data", []),
        ))

    storage = sorted(p for p in providers if p in _STORAGE_OPTIONS)
    if storage:
        suggestions.append(PIISuggestion(
            manifest_field="storage_locations",
            suggested_value=storage,
            confidence="high",
            rationale=f"Personal data was mapped to these stores: {', '.join(storage)}.",
            action="confirm",
            evidence_signals=[s["name"] for s in per_source],
        ))

    if cross_border:
        cats = sorted({c["category"] for c in cross_border})
        regions = sorted({c["region"] for c in cross_border})
        suggestions.append(PIISuggestion(
            manifest_field="cross_border_transfer",
            suggested_value=True,
            confidence="medium",
            rationale=f"Categories {', '.join(cats)} found outside India ({', '.join(regions)}) "
                      f"— review whether this is a cross-border transfer.",
            action="review",
            evidence_signals=[c["source"] for c in cross_border],
        ))

    return {
        "sources": per_source,
        "category_to_sources": category_to_sources,
        "cross_border": cross_border,
        "has_cross_border": bool(cross_border),
        "suggestions": [s.to_dict() for s in suggestions],
    }
