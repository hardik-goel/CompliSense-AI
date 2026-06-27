"""Cron entrypoint for the regulatory-change watcher (Phase 5.4).

Run on a cadence by the host scheduler (Render cron):

    python -m saas.app.regwatch_cron

Fetches every watched legal source, snapshots it, and raises a PENDING change for any diff.
Detection only — a human reviews and decides; rulepacks are never auto-edited.
"""

from __future__ import annotations

import logging

from saas.app.regwatch_api import run_watch_sweep

logger = logging.getLogger(__name__)


def main() -> int:
    summary = run_watch_sweep()
    logger.info("Regwatch sweep: checked=%s changes=%s errors=%s",
                summary["checked"], summary["changes_created"], len(summary["errors"]))
    print(f"regwatch sweep: checked {summary['checked']}, "
          f"{summary['changes_created']} change(s), {len(summary['errors'])} error(s)")
    for c in summary["changes"]:
        print(f"  - CHANGED {c['url']} -> review rules {c.get('rule_ids')}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
