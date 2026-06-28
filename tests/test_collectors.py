"""Agent-side artefact collector (local folder + classifier)."""

import json

from agent.collectors.classifier import Classification, classify, deterministic_classify
from agent.collectors.collect import collect_local
from agent.collectors.local_folder import crawl


def test_deterministic_matches_by_filename_and_keywords():
    c = deterministic_classify("privacy_notice.md", "We process personal data for the stated purpose of processing.")
    assert c.artefact_id == "privacy_notice" and c.confidence > 0.5 and c.method == "deterministic"


def test_deterministic_returns_none_for_unrelated():
    c = deterministic_classify("main.py", "import os\nprint('hello')")
    assert c.artefact_id is None and c.confidence == 0.0


def test_crawl_skips_binary_large_and_skip_dirs(tmp_path):
    (tmp_path / "privacy_notice.md").write_text("personal data, privacy policy")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\x00\x00")           # non-text ext
    big = tmp_path / "huge.txt"; big.write_text("x" * (3 * 1024 * 1024))  # > 2MB cap
    skip = tmp_path / ".git"; skip.mkdir(); (skip / "config.yaml").write_text("retention period")
    rels = {c.rel for c in crawl(str(tmp_path))}
    assert "privacy_notice.md" in rels
    assert "logo.png" not in rels and "huge.txt" not in rels
    assert not any(".git" in r for r in rels)


class _FakeLLM:
    """Classifies by a filename hint; proves the injected-LLM path is used."""
    def available(self): return True
    def classify(self, filename, sample):
        if "retention" in filename.lower():
            return Classification("retention_schedule", 0.9, "fake llm", "llm")
        return Classification(None, 0.1, "fake llm: none", "llm")


def test_collect_stages_matched_and_writes_manifest(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    (src / "retention_schedule.md").write_text("retain personal data 180 days")
    (src / "random.txt").write_text("nothing relevant here")
    out = tmp_path / "out"
    m = collect_local(str(src), str(out), llm=_FakeLLM(), min_confidence=0.6)
    assert m["scanned"] == 2 and m["collected"] == 1
    assert (out / "retention_schedule.md").exists()
    manifest = json.loads((out / "COLLECTION_MANIFEST.json").read_text())
    assert manifest["matched"][0]["artefact_id"] == "retention_schedule"
    assert (out / "READ_ME_FIRST.txt").exists()
    assert m["classifier"] == "llm"


def test_collect_deterministic_when_no_llm(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    (src / "security_policy.md").write_text("encryption at rest, access control, least privilege")
    out = tmp_path / "out"
    m = collect_local(str(src), str(out), llm=None)
    assert m["collected"] == 1 and m["matched"][0]["artefact_id"] == "security_safeguards"
    assert m["classifier"] == "deterministic"


def test_classify_falls_back_on_llm_error(tmp_path):
    class Boom:
        def available(self): return True
        def classify(self, *a): raise RuntimeError("api down")
    c = classify("privacy_notice.md", "personal data privacy policy", llm=Boom())
    assert c.artefact_id == "privacy_notice" and c.method == "deterministic"  # fell back


def test_classify_uses_deterministic_when_llm_unavailable():
    class NoKey:
        def available(self): return False
        def classify(self, *a): raise AssertionError("should not be called")
    c = classify("consent_policy.md", "withdraw consent opt-in", llm=NoKey())
    assert c.artefact_id == "consent_policy" and c.method == "deterministic"


def test_unique_names_avoid_overwrite(tmp_path):
    src = tmp_path / "src"; (src / "a").mkdir(parents=True); (src / "b").mkdir()
    (src / "a" / "privacy_notice.md").write_text("personal data privacy policy purpose of processing")
    (src / "b" / "privacy_notice.md").write_text("personal data privacy policy purpose of processing")
    out = tmp_path / "out"
    m = collect_local(str(src), str(out), llm=None)
    staged = sorted(x["staged_as"] for x in m["matched"])
    assert staged == ["privacy_notice.md", "privacy_notice_2.md"]
