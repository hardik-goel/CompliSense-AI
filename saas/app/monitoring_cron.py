"""Cron entrypoint for scheduled-monitoring sweeps (Phase 2.4).

There is no in-process scheduler — scanning runs client-side and the SaaS has no worker
process. Instead the host scheduler (e.g. a Render cron job) runs this module on a cadence:

    python -m saas.app.monitoring_cron

It runs three sweeps, each deduped per UTC day:

  overdue   projects whose last scan is older than their configured cadence
  stale     generated artefacts the current rulepack has made stale — the client is holding
            a document that no longer matches the law we have recorded
  exposure  pending regulatory-watch changes that touch a document a client holds, before
            any rule has been edited

Regression alerts are raised inline at scan-ingestion time (see monitoring.record_scan_run),
not here.
"""

from __future__ import annotations

import logging

from saas.app.freshness_api import (
    evaluate_artefact_freshness,
    evaluate_regwatch_exposure,
)
from saas.app.monitoring import evaluate_overdue_scans

logger = logging.getLogger(__name__)


def main() -> int:
    """Run every sweep. One failing sweep must not stop the others.

    The sweep list is built here rather than at module level so the names resolve from module
    globals at call time — a module-level tuple would capture the functions at import and
    pin the wiring beyond reach of a test.
    """
    sweeps = (
        ("overdue-scan", evaluate_overdue_scans),
        ("stale-artefact", evaluate_artefact_freshness),
        ("regwatch-exposure", evaluate_regwatch_exposure),
    )
    for label, sweep in sweeps:
        try:
            created = sweep() or []
        except Exception as exc:  # noqa: BLE001 - a cron must not die on one bad sweep
            logger.exception("%s sweep failed", label)
            print(f"{label} sweep: FAILED ({type(exc).__name__}: {exc})")
            continue
        logger.info("%s sweep complete: %d alert(s) raised", label, len(created))
        print(f"{label} sweep: {len(created)} alert(s) raised")
        for alert in created:
            print(f"  - {alert['project_id']}: {alert['message']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
