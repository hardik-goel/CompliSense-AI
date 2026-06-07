"""
Plan and tier configuration for CompliSense-AI.

This module centralizes which features belong to which tier.
Only the FREE tier is enforced in code today; other tiers are
defined as placeholders for future expansion.
"""

from typing import Dict, Any


PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "monthly_scan_limit": 10,
        "max_projects": 2,
        "features": [
            "Core regulatory checks from the selected compliance pack",
            "Local agent + basic SaaS dashboard",
            "Compliance percentage and key issues overview",
        ],
    },
    "standard": {
        "name": "Standard",
        "monthly_scan_limit": None,  # TODO: define
        "max_projects": None,  # TODO: define
        "features": [
            "Everything in Free",
            "Step-by-step remediation guidance for improving coverage and compliance",
            "Expanded rulepack coverage, including more detailed logging and monitoring checks",
            "Basic history and scan comparison in SaaS dashboard (MongoDB required)",
            "Email notifications on scan completion",
        ],
        "status": "TODO",
    },
    "premium": {
        "name": "Premium",
        "monthly_scan_limit": None,  # TODO: define
        "max_projects": None,  # TODO: define
        "features": [
            "Everything in Standard",
            "Advanced evaluators (bias/fairness, explainability, performance drift/robustness)",
            "Team / role-based access control",
            "Rich analytics and trends in SaaS dashboard",
        ],
        "status": "TODO",
    },
    "premium_plus": {
        "name": "Premium+ (Enterprise)",
        "monthly_scan_limit": None,  # Enterprise / contract-specific
        "max_projects": None,
        "features": [
            "Everything in Premium",
            "Multi-tenant SaaS, SSO, detailed audit logs",
            "Custom rule authoring and private rulepacks",
            "On-prem / VPC deployments",
            "SLAs, dedicated support, and proactive compliance reviews",
            "White-glove remediation: help fixing compliance gaps, not just highlighting them",
        ],
        "status": "TODO",
    },
}


def get_plan(tier: str) -> Dict[str, Any]:
    """Return plan configuration for a tier, defaulting to free."""
    return PLANS.get(tier, PLANS["free"])
