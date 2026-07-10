#!/usr/bin/env python3
"""Export the Tier-0 questionnaire to the landing page bundle.

The public /readiness tool renders from this JSON instead of fetching the
backend, which sits on a free Render instance that cold-starts for up to ~30s —
the visitor most likely to hit that cold start is the first-time visitor the
tool exists to convert. Scoring still goes to the API.

`tests/test_manifest.py::test_static_questionnaire_json_matches_source` fails if
this file falls out of sync with `compliance.manifest.QUESTIONS`.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compliance.manifest import get_questionnaire  # noqa: E402

TARGET = ROOT / "landing-page/app/readiness/questionnaire.json"


def main() -> None:
    payload = {"questions": get_questionnaire()}
    TARGET.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(payload['questions'])} questions -> {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
