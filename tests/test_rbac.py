"""RBAC core (Phase 8) — pure."""

from saas.app.rbac import can, role_at_least, role_rank


def test_role_ordering():
    assert role_rank("owner") > role_rank("admin") > role_rank("member") > role_rank("viewer")
    assert role_rank(None) == -1


def test_role_at_least():
    assert role_at_least("admin", "member")
    assert not role_at_least("viewer", "member")
    assert role_at_least("owner", "owner")


def test_permission_matrix():
    assert can("viewer", "view") and can("viewer", "export_evidence")
    assert not can("viewer", "run_scan")
    assert can("member", "run_scan") and not can("member", "manage_members")
    assert can("admin", "manage_members") and not can("admin", "delete_project")
    assert can("owner", "delete_project")


def test_unknown_action_denies():
    assert not can("owner", "launch_missiles")
    assert not can(None, "view")
