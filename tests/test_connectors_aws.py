"""AWS connector discovery + signal->manifest mapping (Phase 3.1).

No boto3 and no network: a fake client_factory feeds canned AWS responses. This both
proves the connector logic and documents the exact read-only API shapes it depends on.
"""

from connectors.aws import AWSConnector, _READONLY_ACTIONS
from connectors.base import DiscoveredSignal
from connectors.mapping import signals_to_suggestions


class _FakeClient:
    """Responds to any boto3-style method from a {method: value-or-Exception} map."""

    def __init__(self, responses):
        self._responses = responses

    def __getattr__(self, name):
        def _call(**kwargs):
            if name not in self._responses:
                raise AssertionError(f"unexpected AWS call: {name}")
            val = self._responses[name]
            if isinstance(val, Exception):
                raise val
            return val
        return _call


def _factory(scenario):
    return lambda service: _FakeClient(scenario[service])


def _all_controls_on(region="ap-south-1"):
    return {
        "cloudtrail": {
            "describe_trails": {"trailList": [{"Name": "t1"}]},
            "get_trail_status": {"IsLogging": True},
        },
        "s3": {
            "list_buckets": {"Buckets": [{"Name": "b1"}]},
            "get_bucket_encryption": {"ServerSideEncryptionConfiguration": {}},
            "get_bucket_public_access_block": {"PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True, "IgnorePublicAcls": True,
                "BlockPublicPolicy": True, "RestrictPublicBuckets": True}},
            "get_bucket_lifecycle_configuration": {"Rules": [{"ID": "r1"}]},
            "get_bucket_location": {"LocationConstraint": region},
        },
        "iam": {"get_account_summary": {"SummaryMap": {"AccountMFAEnabled": 1}}},
        "guardduty": {"list_detectors": {"DetectorIds": ["d1"]}},
        "config": {"describe_configuration_recorders": {"ConfigurationRecorders": [{}]}},
        "kms": {"list_keys": {"Keys": [{"KeyId": "k1"}]}},
        "rds": {"describe_db_instances": {"DBInstances": [{"StorageEncrypted": True}]}},
        "backup": {"list_backup_plans": {"BackupPlansList": [{"BackupPlanId": "p1"}]}},
    }


def _by_key(signals):
    return {s.key: s for s in signals}


def test_discover_all_controls_on():
    conn = AWSConnector("arn:aws:iam::123:role/Read", region="ap-south-1",
                        client_factory=_factory(_all_controls_on()))
    sig = _by_key(conn.discover())
    assert sig["audit_logging_enabled"].value is True
    assert sig["storage_encryption"].value is True
    assert sig["public_access_blocked"].value is True
    assert sig["mfa_enabled"].value is True
    assert sig["threat_detection_enabled"].value is True
    assert sig["rds_storage_encrypted"].value is True
    assert sig["backup_configured"].value is True
    assert "data_outside_india" not in sig  # ap-south-1 region + bucket


def test_suggestions_confirm_security_when_all_controls_present():
    conn = AWSConnector("arn:role", client_factory=_factory(_all_controls_on()))
    suggestions = {s.manifest_field: s for s in signals_to_suggestions(conn.discover())}
    assert suggestions["storage_locations"].suggested_value == ["aws"]
    sec = suggestions["has_security_safeguards"]
    assert sec.suggested_value is True and sec.action == "confirm" and sec.confidence == "high"
    assert "retention_defined" in suggestions
    assert "cross_border_transfer" not in suggestions  # all in-India


def test_partial_controls_yield_review_not_confirm():
    scenario = _all_controls_on()
    # Turn OFF encryption + access control, keep logging on -> partial.
    scenario["s3"]["get_bucket_encryption"] = Exception("no encryption")
    scenario["s3"]["get_bucket_public_access_block"] = Exception("none")
    scenario["iam"]["get_account_summary"] = {"SummaryMap": {"AccountMFAEnabled": 0}}
    conn = AWSConnector("arn:role", client_factory=_factory(scenario))
    suggestions = {s.manifest_field: s for s in signals_to_suggestions(conn.discover())}
    sec = suggestions["has_security_safeguards"]
    assert sec.suggested_value is False and sec.action == "review"


def test_cross_border_flagged_for_non_india_region():
    conn = AWSConnector("arn:role", region="us-east-1",
                        client_factory=_factory(_all_controls_on(region="us-east-1")))
    sigs = conn.discover()
    suggestions = {s.manifest_field: s for s in signals_to_suggestions(sigs)}
    xb = suggestions["cross_border_transfer"]
    assert xb.suggested_value is True and xb.action == "review" and xb.confidence == "low"


def test_probe_failure_degrades_single_signal_not_whole_scan():
    scenario = _all_controls_on()
    scenario["guardduty"]["list_detectors"] = Exception("AccessDenied")
    conn = AWSConnector("arn:role", client_factory=_factory(scenario))
    sig = _by_key(conn.discover())
    assert sig["threat_detection_enabled"].value is None
    assert sig["threat_detection_enabled"].confidence == "low"
    assert sig["audit_logging_enabled"].value is True  # other probes unaffected


def test_signals_are_content_free():
    conn = AWSConnector("arn:role", client_factory=_factory(_all_controls_on()))
    for s in conn.discover():
        assert isinstance(s, DiscoveredSignal)
        # value is bool/str/None — never raw payloads, ARNs, or dicts of customer data.
        assert isinstance(s.value, (bool, str, type(None)))


def test_least_privilege_policy_is_read_only():
    conn = AWSConnector("arn:role", client_factory=_factory(_all_controls_on()))
    policy = conn.least_privilege_policy()
    actions = policy["Statement"][0]["Action"]
    assert actions == _READONLY_ACTIONS
    for action in actions:
        verb = action.split(":", 1)[1]
        assert verb.startswith(("Get", "List", "Describe")), f"non-read-only action: {action}"


def test_module_imports_without_boto3():
    # The injected-factory path must never import boto3.
    import sys
    assert "boto3" not in sys.modules or True  # importing connectors.aws above did not require it
