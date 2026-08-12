"""LLM classifier provider selection + OpenAI-compatible (OpenRouter) adapter."""

from agent.collectors.classifier import OpenAICompatibleClassifier, default_classifier


def test_default_classifier_none_without_keys(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert default_classifier() is None
    assert default_classifier(no_llm=True) is None


def test_default_classifier_prefers_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    c = default_classifier()
    assert isinstance(c, OpenAICompatibleClassifier) and c.available()
    assert "openrouter.ai" in c.base_url


def test_openai_compatible_classify_parses(monkeypatch):
    captured = {}

    class _Resp:
        def json(self):
            return {"choices": [{"message": {"content":
                    '{"artefact_id":"privacy_notice","confidence":0.88,"reason":"ok"}'}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["model"] = json["model"]
        return _Resp()

    import requests
    monkeypatch.setattr(requests, "post", fake_post)
    clf = OpenAICompatibleClassifier(api_key="sk-or-x", model="anthropic/claude-3.5-haiku")
    out = clf.classify("privacy_notice.md", "personal data")
    assert out.artefact_id == "privacy_notice" and out.method == "llm"
    assert captured["url"].endswith("/chat/completions") and captured["model"] == "anthropic/claude-3.5-haiku"
