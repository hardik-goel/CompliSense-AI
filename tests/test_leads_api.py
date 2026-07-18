"""Lead capture endpoint (Prompt 3, Tasks 2 + 4)."""

import asyncio
import datetime as dt
import types

import pytest

import saas.app.leads_api as L
from saas.app.mail import MailMessage


def _run(coro):
    return asyncio.run(coro)


class _Col:
    def __init__(self):
        self.docs = []
    def insert_one(self, d):
        self.docs.append(d)
    def count_documents(self, q):
        # supports {"ip": x, "created_at": {"$gte": t}}
        ip = q.get("ip")
        return sum(1 for d in self.docs if d.get("ip") == ip)
    def delete_many(self, q):
        email = q.get("email")
        before = len(self.docs)
        self.docs = [d for d in self.docs if d.get("email") != email]
        class R:  # noqa
            deleted_count = before - len(self.docs)
        return R()


class _FakeMailer:
    def __init__(self):
        self.sent = []
    def send(self, message: MailMessage) -> bool:
        self.sent.append(message)
        return True


class _Req:
    def __init__(self, ip="1.2.3.4"):
        self.headers = {}
        class C:  # noqa
            host = ip
        self.client = C()


def _patch(monkeypatch, operator="ops@complisenseai.com"):
    col = _Col()
    mailer = _FakeMailer()
    monkeypatch.setattr(L, "leads_collection", lambda: col)
    monkeypatch.setattr(L, "get_mailer", lambda: mailer)
    # settings is a frozen dataclass — swap the whole reference for a namespace.
    monkeypatch.setattr(L, "settings", types.SimpleNamespace(
        operator_notify_email=operator,
        support_email="support@complisenseai.com",
        direct_demo_url="",
        mail_from="support@complisenseai.com",
    ))
    return col, mailer


PERSONA = {"entity_type": "startup", "sector": "saas", "has_privacy_notice": True,
           "has_breach_process": False}


def _req(email="founder@startup.example", consent=True, honeypot="", pack="dpdp_india_core_v1"):
    return L.LeadRequest(email=email, answers=PERSONA, pack_id=pack, consent=consent,
                         company_website=honeypot)


def test_valid_lead_persists_and_dual_delivers(monkeypatch):
    col, mailer = _patch(monkeypatch)
    out = _run(L.capture_lead(_req(), _Req()))
    assert out["ok"] and out["readiness_score"] is not None
    assert len(col.docs) == 1 and col.docs[0]["email"] == "founder@startup.example"
    # consent timestamp recorded (DPDP)
    assert col.docs[0]["consent"] is True and isinstance(col.docs[0]["consent_at"], dt.datetime)
    # both visitor + operator emailed
    recipients = [m.to[0] for m in mailer.sent]
    assert "founder@startup.example" in recipients
    assert "ops@complisenseai.com" in recipients
    # score email carries the legal footer + prepare-by framing
    visitor = next(m for m in mailer.sent if m.to[0] == "founder@startup.example")
    assert "not legal advice" in visitor.html.lower() and "13 May 2027" in visitor.html


def test_consent_required(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(L.capture_lead(_req(consent=False), _Req()))
    assert e.value.status_code == 400 and "consent" in e.value.detail.lower()


def test_invalid_email_rejected(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(L.capture_lead(_req(email="not-an-email"), _Req()))
    assert e.value.status_code == 400


def test_honeypot_silently_drops(monkeypatch):
    col, mailer = _patch(monkeypatch)
    out = _run(L.capture_lead(_req(honeypot="http://spam.example"), _Req()))
    assert out["ok"] and out["delivered"] is False
    assert col.docs == [] and mailer.sent == []  # nothing stored or sent


def test_rate_limit(monkeypatch):
    from fastapi import HTTPException
    col, _ = _patch(monkeypatch)
    for _ in range(L._RATE_LIMIT_MAX):
        _run(L.capture_lead(_req(), _Req(ip="9.9.9.9")))
    with pytest.raises(HTTPException) as e:
        _run(L.capture_lead(_req(), _Req(ip="9.9.9.9")))
    assert e.value.status_code == 429


def test_operator_optional(monkeypatch):
    col, mailer = _patch(monkeypatch, operator="")  # no operator configured
    _run(L.capture_lead(_req(), _Req()))
    assert [m.to[0] for m in mailer.sent] == ["founder@startup.example"]  # only visitor


def test_delete_lead_path(monkeypatch):
    col, _ = _patch(monkeypatch)
    _run(L.capture_lead(_req(email="erase@me.example"), _Req()))
    out = _run(L.delete_lead(email="erase@me.example", _admin=True))
    assert out["deleted"] == 1 and col.docs == []
