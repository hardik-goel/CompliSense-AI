"""Connector registry (Phase 3.1).

One lookup the API layer (Phase 3.2) uses to instantiate a connector by provider id,
and to advertise which providers exist + what credentials each needs. Adding a connector
is a one-line registration here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Type

from connectors.aws import AWSConnector
from connectors.azure import AzureConnector
from connectors.base import Connector, ConnectorError
from connectors.gcp import GCPConnector
from connectors.github import GitHubConnector

CONNECTORS: Dict[str, Type[Connector]] = {
    AWSConnector.provider: AWSConnector,
    GCPConnector.provider: GCPConnector,
    AzureConnector.provider: AzureConnector,
    GitHubConnector.provider: GitHubConnector,
}

# What each connector needs to run — surfaced to the UI so it can collect the right inputs.
CONNECTOR_REQUIREMENTS: Dict[str, List[str]] = {
    "aws": ["role_arn", "region", "external_id (optional)"],
    "gcp": ["project_id", "access_token", "region"],
    "azure": ["subscription_id", "access_token"],
    "github": ["org", "token"],
}


def available_providers() -> List[str]:
    return list(CONNECTORS.keys())


def get_connector(provider: str, **kwargs: Any) -> Connector:
    """Instantiate a connector by provider id. Raises ConnectorError for unknown ids."""
    cls = CONNECTORS.get(provider)
    if cls is None:
        raise ConnectorError(f"Unknown connector provider '{provider}'. Available: {available_providers()}")
    return cls(**kwargs)
