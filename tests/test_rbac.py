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


def test_named_roles_engineer_and_dpo():
    # Engineer = the doer: scans/edits/assigns/copilot, but cannot sign off or manage members.
    assert can("engineer", "run_scan") and can("engineer", "assign_gap") and can("engineer", "use_copilot")
    assert not can("engineer", "sign_off_gap") and not can("engineer", "manage_members")
    # DPO = governance/attestation: assigns + signs off + sets schedule, but does not edit/scan.
    assert can("dpo", "sign_off_gap") and can("dpo", "assign_gap") and can("dpo", "manage_schedule")
    assert can("dpo", "export_evidence") and not can("dpo", "run_scan") and not can("dpo", "manage_members")
    # member is an alias of engineer
    assert can("member", "run_scan") and not can("member", "sign_off_gap")


def test_unknown_action_denies():
    assert not can("owner", "launch_missiles")
    assert not can(None, "view")
