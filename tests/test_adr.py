"""The ADR set is part of the product, so it is kept honest by tests rather than by habit.

A decision record that drifts from the code is worse than none: it tells a reviewer — an
auditor, a CTO in diligence, a new engineer — something that is no longer true. These tests
enforce the structural invariants a reader relies on.
"""

import re
from pathlib import Path

import pytest

ADR_DIR = Path("docs/adr")
ADR_RE = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
REQUIRED_SECTIONS = ("## Status", "## Context", "## Decision", "## Consequences",
                     "## Alternatives considered")


def adr_files():
    return sorted(p for p in ADR_DIR.glob("*.md") if ADR_RE.match(p.name))


def test_the_adr_directory_exists_and_is_not_empty():
    assert adr_files(), "No ADRs found in docs/adr/"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_every_adr_carries_the_required_sections(path):
    text = path.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    assert not missing, f"{path.name} is missing {missing}"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_every_adr_declares_a_recognised_status(path):
    text = path.read_text(encoding="utf-8")
    status_block = text.split("## Status", 1)[1].split("##", 1)[0]
    assert any(s in status_block for s in ("Accepted", "Superseded", "Proposed", "Deprecated")), \
        f"{path.name} has no recognised status"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_every_adr_starts_with_a_numbered_title(path):
    first = path.read_text(encoding="utf-8").lstrip().splitlines()[0]
    assert first.startswith("# ADR "), f"{path.name} does not start with '# ADR NNNN — ...'"


def test_adr_numbers_are_unique_and_contiguous_from_one():
    numbers = [int(ADR_RE.match(p.name).group(1)) for p in adr_files()]
    assert len(numbers) == len(set(numbers)), "Duplicate ADR numbers"
    assert numbers == list(range(1, len(numbers) + 1)), f"ADR numbering has a gap: {numbers}"


def test_the_index_lists_every_adr():
    index = (ADR_DIR / "README.md").read_text(encoding="utf-8")
    missing = [p.name for p in adr_files() if p.name not in index]
    assert not missing, f"docs/adr/README.md does not link {missing}"


def test_the_index_does_not_link_an_adr_that_no_longer_exists():
    index = (ADR_DIR / "README.md").read_text(encoding="utf-8")
    known = {p.name for p in adr_files()}
    linked = set(re.findall(r"\((\d{4}-[a-z0-9-]+\.md)\)", index))
    assert not (linked - known), f"Index links missing ADRs: {sorted(linked - known)}"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_no_adr_claims_the_product_determines_compliance(path):
    """The whole product is readiness-framed; an ADR must not undercut that in writing."""
    text = path.read_text(encoding="utf-8").lower()
    for phrase in ("guarantees compliance", "ensures compliance", "certifies compliance"):
        assert phrase not in text, f"{path.name} contains forbidden claim: {phrase!r}"
