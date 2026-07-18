from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_cors_origins() -> str:
    configured = os.getenv("CORS_ORIGINS")
    if configured:
        return configured
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        return ",".join(
            [
                "https://complisenseai.com",
                "https://www.complisenseai.com",
                "https://complisense-ai-backend.onrender.com",
                "https://api.complisenseai.com",
            ]
        )
    return "*"


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CompliSense-AI SaaS")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    marketing_site_url: str = os.getenv("MARKETING_SITE_URL", "https://complisenseai.com")
    app_base_url: str = os.getenv("APP_BASE_URL", "https://complisense-ai-backend.onrender.com")
    api_base_url: str = os.getenv("API_BASE_URL", "https://api.complisenseai.com")
    support_email: str = os.getenv("SUPPORT_EMAIL", "support@complisenseai.com")
    cookie_domain: str | None = os.getenv("COOKIE_DOMAIN", ".complisenseai.com")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "complisense")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    admin_api_token: str = os.getenv("ADMIN_API_TOKEN", "dev-admin-token")
    cors_origins: str = _default_cors_origins()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    port: int = int(os.getenv("PORT", "10000"))
    secure_cookies: bool = _to_bool(os.getenv("SECURE_COOKIES"), default=False)
    # ── Lead capture + mail (Prompt 3) ──────────────────────────────────────────
    # MAIL_PROVIDER: smtp | console | none. "console" logs the email (dev/no creds);
    # "none" disables sending (score still returned). A provider like Postmark/SES can be
    # added by implementing the Mailer interface in saas/app/mail.py.
    mail_provider: str = os.getenv("MAIL_PROVIDER", "console")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = _to_bool(os.getenv("SMTP_USE_TLS"), default=True)
    mail_from: str = os.getenv("MAIL_FROM", os.getenv("SUPPORT_EMAIL", "support@complisenseai.com"))
    operator_notify_email: str = os.getenv("OPERATOR_NOTIFY_EMAIL", "")
    # Ungated direct calendar link for warm inbound (investors/referrals). NOT surfaced on
    # the public page — shared manually. The public "Book a Demo" is gated behind the test.
    direct_demo_url: str = os.getenv("DIRECT_DEMO_URL", "")
    # Lead privacy contact + retention (DPDP compliance for the lead form itself).
    lead_privacy_contact: str = os.getenv("LEAD_PRIVACY_CONTACT", os.getenv("SUPPORT_EMAIL", "support@complisenseai.com"))
    lead_retention_days: int = int(os.getenv("LEAD_RETENTION_DAYS", "365"))

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def marketing_host(self) -> str:
        return self.marketing_site_url.removeprefix("https://").removeprefix("http://").split("/", 1)[0]

    @property
    def app_host(self) -> str:
        return self.app_base_url.removeprefix("https://").removeprefix("http://").split("/", 1)[0]

    @property
    def api_host(self) -> str:
        return self.api_base_url.removeprefix("https://").removeprefix("http://").split("/", 1)[0]

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


# ── Security hardening: never allow weak default secrets in production ───────────
# (Audit finding H7.) In development these defaults stay for convenience but are warned
# about; in production a weak/unset secret is a hard startup failure, not a silent fallback.
import logging as _logging

_WEAK_SECRETS = {
    "admin_api_token": "dev-admin-token",
    "jwt_secret": "change-me-in-production",
}


def _validate_secrets(s: Settings) -> None:
    _log = _logging.getLogger("complisense.config")
    weak = [name for name, bad in _WEAK_SECRETS.items() if getattr(s, name) == bad]
    if not weak:
        return
    if s.is_production:
        raise RuntimeError(
            "Refusing to start in production with weak/default secrets: "
            + ", ".join(weak)
            + ". Set strong values via environment variables "
            + ", ".join(n.upper() for n in weak)
            + "."
        )
    _log.warning(
        "Using insecure default secret(s) %s — acceptable only in development. "
        "Set %s before any production deployment.",
        ", ".join(weak),
        ", ".join(n.upper() for n in weak),
    )


_validate_secrets(settings)
