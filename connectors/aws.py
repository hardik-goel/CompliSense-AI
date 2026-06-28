"""AWS read-only discovery connector (Phase 3.1).

Access model: **cross-account STS AssumeRole**. The customer deploys a read-only IAM
role (from the policy ``least_privilege_policy`` publishes) that trusts our account; we
assume it per-scan to obtain short-lived credentials and discard them after discovery.
No long-lived keys, no credential storage.

``boto3`` is an OPTIONAL dependency: this module imports cleanly without it. A
``client_factory`` can be injected (used by tests and by callers that manage their own
session); only the default factory needs boto3 and only at call time.

Every probe is read-only and defensively wrapped: a permission/throttling failure on one
control degrades that single signal (value ``None``, low confidence) instead of failing
the whole scan.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Dict, List, Optional

from connectors.base import Connector, ConnectorError, DiscoveredSignal, utc_now_iso

# Indian AWS regions — resources/usage outside these hint at a possible cross-border
# transfer worth human review (never asserted automatically).
INDIA_REGIONS = {"ap-south-1", "ap-south-2"}

# Read-only actions the customer grants. Strictly Get/List/Describe — published so the
# customer can audit that we ask for nothing that can mutate their account.
_READONLY_ACTIONS = [
    "cloudtrail:DescribeTrails",
    "cloudtrail:GetTrailStatus",
    "s3:ListAllMyBuckets",
    "s3:GetBucketEncryption",
    "s3:GetBucketPublicAccessBlock",
    "s3:GetBucketLocation",
    "s3:GetLifecycleConfiguration",
    "s3:GetAccountPublicAccessBlock",
    "iam:GetAccountSummary",
    "iam:GetAccountPasswordPolicy",
    "guardduty:ListDetectors",
    "config:DescribeConfigurationRecorders",
    "config:DescribeConfigurationRecorderStatus",
    "kms:ListKeys",
    "rds:DescribeDBInstances",
    "backup:ListBackupPlans",
    "ec2:DescribeRegions",
]

ClientFactory = Callable[[str], Any]


class AWSConnector(Connector):
    provider = "aws"

    def __init__(
        self,
        role_arn: str,
        region: str = "ap-south-1",
        external_id: Optional[str] = None,
        client_factory: Optional[ClientFactory] = None,
        session_name: str = "complisense-discovery",
        now: Optional[dt.datetime] = None,
    ):
        self.role_arn = role_arn
        self.region = region
        self.external_id = external_id
        self.session_name = session_name
        self._injected_factory = client_factory
        self._now_iso = utc_now_iso(now)
        self._assumed: Optional[Dict[str, str]] = None

    # ── credential handling ──────────────────────────────────────────────────
    def _assume_role(self) -> Dict[str, str]:
        """Assume the customer's read-only role once; reuse temp creds across clients."""
        if self._assumed is not None:
            return self._assumed
        try:
            import boto3  # local import: optional dependency
        except ImportError as exc:  # pragma: no cover - exercised only without boto3
            raise ConnectorError("boto3 is required for live AWS discovery") from exc

        sts = boto3.client("sts", region_name=self.region)
        kwargs: Dict[str, Any] = {"RoleArn": self.role_arn, "RoleSessionName": self.session_name}
        if self.external_id:
            kwargs["ExternalId"] = self.external_id
        try:
            creds = sts.assume_role(**kwargs)["Credentials"]
        except Exception as exc:  # boto3 ClientError etc.
            raise ConnectorError(f"Failed to assume role {self.role_arn}: {exc}") from exc
        self._assumed = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
        return self._assumed

    def _client(self, service: str) -> Any:
        if self._injected_factory is not None:
            return self._injected_factory(service)
        import boto3  # local import: optional dependency
        return boto3.client(service, region_name=self.region, **self._assume_role())

    def _signal(self, key: str, value: Any, confidence: str, evidence: str) -> DiscoveredSignal:
        return DiscoveredSignal(
            key=key, value=value, source=self.provider, confidence=confidence,
            evidence=evidence, observed_at=self._now_iso,
        )

    def _degraded(self, key: str, exc: Exception) -> DiscoveredSignal:
        return self._signal(key, None, "low", f"could not read (permission or service error): {type(exc).__name__}")

    # ── discovery ────────────────────────────────────────────────────────────
    def discover(self) -> List[DiscoveredSignal]:
        probes = [
            self._probe_cloudtrail,
            self._probe_s3,
            self._probe_iam_mfa,
            self._probe_guardduty,
            self._probe_config,
            self._probe_kms,
            self._probe_rds,
            self._probe_backup,
            self._probe_regions,
        ]
        signals: List[DiscoveredSignal] = []
        for probe in probes:
            signals.extend(probe())
        return signals

    def _probe_cloudtrail(self) -> List[DiscoveredSignal]:
        try:
            client = self._client("cloudtrail")
            trails = client.describe_trails().get("trailList", [])
            logging_on = False
            for trail in trails:
                name = trail.get("Name") or trail.get("TrailARN")
                try:
                    if name and client.get_trail_status(Name=name).get("IsLogging"):
                        logging_on = True
                        break
                except Exception:
                    continue
            return [self._signal(
                "audit_logging_enabled", logging_on, "high" if trails else "medium",
                f"{len(trails)} CloudTrail trail(s); logging active={logging_on}",
            )]
        except Exception as exc:
            return [self._degraded("audit_logging_enabled", exc)]

    def _probe_s3(self) -> List[DiscoveredSignal]:
        out: List[DiscoveredSignal] = []
        try:
            s3 = self._client("s3")
            buckets = s3.list_buckets().get("Buckets", [])
            out.append(self._signal("has_data_stores", bool(buckets), "high",
                                    f"{len(buckets)} S3 bucket(s) present"))
            enc_all = True
            block_all = True
            lifecycle_any = False
            non_india = False
            for b in buckets:
                name = b.get("Name")
                if not name:
                    continue
                try:
                    s3.get_bucket_encryption(Bucket=name)
                except Exception:
                    enc_all = False
                try:
                    pab = s3.get_bucket_public_access_block(Bucket=name).get("PublicAccessBlockConfiguration", {})
                    if not all(pab.get(k) for k in ("BlockPublicAcls", "IgnorePublicAcls",
                                                    "BlockPublicPolicy", "RestrictPublicBuckets")):
                        block_all = False
                except Exception:
                    block_all = False
                try:
                    rules = s3.get_bucket_lifecycle_configuration(Bucket=name).get("Rules", [])
                    if rules:
                        lifecycle_any = True
                except Exception:
                    pass
                try:
                    loc = s3.get_bucket_location(Bucket=name).get("LocationConstraint")
                    region = loc or "us-east-1"  # null constraint == us-east-1
                    if region not in INDIA_REGIONS:
                        non_india = True
                except Exception:
                    pass
            if buckets:
                out.append(self._signal("storage_encryption", enc_all, "high",
                                        "default encryption on all buckets" if enc_all else "one or more buckets without default encryption"))
                out.append(self._signal("public_access_blocked", block_all, "high",
                                        "public access blocked on all buckets" if block_all else "one or more buckets not fully blocked"))
                out.append(self._signal("retention_lifecycle_present", lifecycle_any, "medium",
                                        "S3 lifecycle/retention rules present" if lifecycle_any else "no S3 lifecycle rules found"))
                if non_india:
                    out.append(self._signal("data_outside_india", True, "low",
                                            "S3 data found in a non-Indian region — review for cross-border transfer"))
            return out
        except Exception as exc:
            return [self._degraded("has_data_stores", exc)]

    def _probe_iam_mfa(self) -> List[DiscoveredSignal]:
        try:
            iam = self._client("iam")
            summary = iam.get_account_summary().get("SummaryMap", {})
            mfa_on_root = bool(summary.get("AccountMFAEnabled"))
            return [self._signal("mfa_enabled", mfa_on_root, "medium",
                                 "root account MFA enabled" if mfa_on_root else "root account MFA not enabled")]
        except Exception as exc:
            return [self._degraded("mfa_enabled", exc)]

    def _probe_guardduty(self) -> List[DiscoveredSignal]:
        try:
            gd = self._client("guardduty")
            detectors = gd.list_detectors().get("DetectorIds", [])
            return [self._signal("threat_detection_enabled", bool(detectors), "high",
                                 f"{len(detectors)} GuardDuty detector(s)")]
        except Exception as exc:
            return [self._degraded("threat_detection_enabled", exc)]

    def _probe_config(self) -> List[DiscoveredSignal]:
        try:
            cfg = self._client("config")
            recorders = cfg.describe_configuration_recorders().get("ConfigurationRecorders", [])
            return [self._signal("config_recording_enabled", bool(recorders), "medium",
                                 f"{len(recorders)} AWS Config recorder(s)")]
        except Exception as exc:
            return [self._degraded("config_recording_enabled", exc)]

    def _probe_kms(self) -> List[DiscoveredSignal]:
        try:
            kms = self._client("kms")
            keys = kms.list_keys().get("Keys", [])
            return [self._signal("encryption_keys_present", bool(keys), "medium",
                                 f"{len(keys)} KMS key(s)")]
        except Exception as exc:
            return [self._degraded("encryption_keys_present", exc)]

    def _probe_rds(self) -> List[DiscoveredSignal]:
        try:
            rds = self._client("rds")
            instances = rds.describe_db_instances().get("DBInstances", [])
            encrypted_all = bool(instances) and all(i.get("StorageEncrypted") for i in instances)
            sigs = [self._signal("rds_present", bool(instances), "high", f"{len(instances)} RDS instance(s)")]
            if instances:
                sigs.append(self._signal("rds_storage_encrypted", encrypted_all, "high",
                                         "all RDS instances encrypted at rest" if encrypted_all else "one or more RDS instances unencrypted"))
            return sigs
        except Exception as exc:
            return [self._degraded("rds_present", exc)]

    def _probe_backup(self) -> List[DiscoveredSignal]:
        try:
            backup = self._client("backup")
            plans = backup.list_backup_plans().get("BackupPlansList", [])
            return [self._signal("backup_configured", bool(plans), "medium",
                                 f"{len(plans)} AWS Backup plan(s)")]
        except Exception as exc:
            return [self._degraded("backup_configured", exc)]

    def _probe_regions(self) -> List[DiscoveredSignal]:
        # The connector region itself is a cross-border hint if outside India.
        outside = self.region not in INDIA_REGIONS
        return [self._signal("primary_region", self.region,
                             "high", f"discovery region {self.region}"
                             + (" (outside India — review cross-border)" if outside else ""))]

    # ── policy ───────────────────────────────────────────────────────────────
    def least_privilege_policy(self) -> Dict[str, Any]:
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "CompliSenseReadOnlyDiscovery",
                    "Effect": "Allow",
                    "Action": list(_READONLY_ACTIONS),
                    "Resource": "*",
                }
            ],
        }
