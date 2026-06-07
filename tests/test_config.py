import importlib


def test_production_defaults_to_complisense_domains(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    config_module = importlib.import_module("saas.app.config")
    config_module = importlib.reload(config_module)

    assert config_module.settings.cors_origin_list == [
        "https://complisenseai.com",
        "https://www.complisenseai.com",
        "https://complisense-ai-backend.onrender.com",
        "https://api.complisenseai.com",
    ]


def test_domain_defaults(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("MARKETING_SITE_URL", raising=False)
    monkeypatch.delenv("COOKIE_DOMAIN", raising=False)

    config_module = importlib.import_module("saas.app.config")
    config_module = importlib.reload(config_module)

    assert config_module.settings.marketing_site_url == "https://complisenseai.com"
    assert config_module.settings.app_base_url == "https://complisense-ai-backend.onrender.com"
    assert config_module.settings.api_base_url == "https://api.complisenseai.com"
    assert config_module.settings.cookie_domain == ".complisenseai.com"
