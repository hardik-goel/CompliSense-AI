"""Cron entrypoint for scheduled-monitoring sweeps (Phase 2.4).

There is no in-process scheduler — scanning runs client-side and the SaaS has no worker
process. Instead the host scheduler (e.g. a Render cron job) runs this module on a cadence:

    python -m saas.app.monitoring_cron

It evaluates every project with a monitoring schedule and raises a scan-overdue alert when
the last scan is older than the configured cadence (deduped per UTC day). Regression alerts
are raised inline at scan-ingestion time (see monitoring.record_scan_run), not here.
"""

from __future__ import annotations

import logging

from saas.app.monitoring import evaluate_overdue_scans

logger = logging.getLogger(__name__)


def main() -> int:
    created = evaluate_overdue_scans()
    logger.info("Overdue-scan sweep complete: %d alert(s) raised", len(created))
    print(f"overdue-scan sweep: {len(created)} alert(s) raised")
    for alert in created:
        print(f"  - {alert['project_id']}: {alert['message']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
