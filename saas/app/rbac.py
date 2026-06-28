"""Role-based access control core (Phase 8) — pure, no I/O.

Domain-named team roles with explicit permission sets:

  - **viewer**   — read + export evidence.
  - **engineer** — build/scan/edit + assign gaps + use the copilot (the "doer").
  - **member**   — alias of engineer (kept for backward compatibility with existing teams).
  - **dpo**      — Data Protection Officer: the governance/attestation authority. Assigns
                   gaps, **signs off** gaps, sets the monitoring schedule — but does not edit
                   the project or run scans.
  - **admin**    — everything below + manage members.
  - **owner**    — admin + delete the project.

Permission is an explicit set membership (not a single rank), so the DPO can sign off without
being an admin. ``can()`` fails closed: an unknown role or action denies.
"""

from __future__ import annotations

from typing import Optional, Set

# Ordered low→high for display / role_at_least; permissions are set-based (below), not rank-based.
ROLES = ("viewer", "engineer", "member", "dpo", "admin", "owner")
_RANK = {role: i for i, role in enumerate(ROLES)}

_VIEWER: Set[str] = {"view", "export_evidence"}
_ENGINEER: Set[str] = _VIEWER | {"run_scan", "edit_project", "assign_gap", "use_copilot"}
_DPO: Set[str] = _VIEWER | {"assign_gap", "sign_off_gap", "manage_schedule"}
_ADMIN: Set[str] = _ENGINEER | _DPO | {"manage_members"}
_OWNER: Set[str] = _ADMIN | {"delete_project"}

ROLE_PERMISSIONS = {
    "viewer": _VIEWER,
    "engineer": _ENGINEER,
    "member": _ENGINEER,   # alias
    "dpo": _DPO,
    "admin": _ADMIN,
    "owner": _OWNER,
}

# All actions the system knows about (for validation / docs).
ALL_ACTIONS = set().union(*ROLE_PERMISSIONS.values())


def role_rank(role: Optional[str]) -> int:
    return _RANK.get(role or "", -1)


def role_at_least(role: Optional[str], minimum: str) -> bool:
    return role_rank(role) >= role_rank(minimum)


def can(role: Optional[str], action: str) -> bool:
    """True if ``role`` may perform ``action``. Fails closed (unknown role/action → False)."""
    return action in ROLE_PERMISSIONS.get(role or "", set())
