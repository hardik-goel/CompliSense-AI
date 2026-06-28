"""Role-based access control core (Phase 8) — pure, no I/O.

Four roles in a strict hierarchy; each action requires a minimum role. Project access is
either the legacy single owner (the project's ``user_id``) or a team member whose role meets
the action's minimum. Keeping this pure makes the permission matrix trivially testable and
the same check reusable across endpoints.
"""

from __future__ import annotations

from typing import Optional

ROLES = ("viewer", "member", "admin", "owner")
_RANK = {role: i for i, role in enumerate(ROLES)}

# Action -> minimum role that may perform it.
ACTION_MIN_ROLE = {
    "view": "viewer",
    "export_evidence": "viewer",
    "run_scan": "member",
    "edit_project": "member",
    "use_copilot": "member",
    "manage_members": "admin",
    "manage_schedule": "admin",
    "delete_project": "owner",
}


def role_rank(role: Optional[str]) -> int:
    return _RANK.get(role or "", -1)


def role_at_least(role: Optional[str], minimum: str) -> bool:
    return role_rank(role) >= role_rank(minimum)


def can(role: Optional[str], action: str) -> bool:
    """True if ``role`` may perform ``action``. Unknown action denies (fail-closed)."""
    minimum = ACTION_MIN_ROLE.get(action)
    if minimum is None:
        return False
    return role_at_least(role, minimum)
