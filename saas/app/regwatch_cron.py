"""Cron entrypoint for the regulatory-change watcher (Phase 5.4).

Run on a cadence by the host scheduler (Render cron):

    python -m saas.app.regwatch_cron

Two automated stages, both human-gated downstream:
1. **Detect** — fetch every watched source, snapshot it, raise a PENDING change for any diff.
2. **Draft** — for each un-drafted pending change, run the (injectable) LLM to summarise the
   change and write a DRAFT patch stub under ``rulepacks/proposals/`` — applied to NOTHING.

Approval + merge of a draft is a strictly human step (regwatch API). Rulepacks are never
auto-edited by this cron.
"""

from __future__ import annotations

import logging
import os

from saas.app.regwatch_api import draft_pending_changes, run_watch_sweep

logger = logging.getLogger(__name__)


def _cron_llm():
    """Build the drafting LLM, or None when no API key is configured (detection still runs)."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.info("No ANTHROPIC_API_KEY — skipping LLM drafting (detection only).")
        return None
    try:
        from compliance.copilot import default_llm
        return default_llm()
    except Exception as exc:  # never let drafting setup break the sweep
        logger.warning("Could not build drafting LLM: %s", exc)
        return None


def main() -> int:
    summary = run_watch_sweep()
    logger.info("Regwatch sweep: checked=%s changes=%s errors=%s",
                summary["checked"], summary["changes_created"], len(summary["errors"]))
    print(f"regwatch sweep: checked {summary['checked']}, "
          f"{summary['changes_created']} change(s), {len(summary['errors'])} error(s)")
    for c in summary["changes"]:
        print(f"  - CHANGED {c['url']} -> review rules {c.get('rule_ids')}")

    # Automated DRAFT pass (writes proposal stubs only; never a live rulepack).
    draft_summary = draft_pending_changes(llm=_cron_llm())
    logger.info("Regwatch draft: drafted=%s", draft_summary["drafted"])
    print(f"regwatch draft: {draft_summary['drafted']} proposal(s) drafted "
          f"(staged for human review; no rulepack edited)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
