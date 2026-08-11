"""The records page — the surface that makes ROPA/DFD/domains/freshness visible at all.

Until this existed, every one of those features was reachable only by curl.
"""

import asyncio

import pytest
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

import saas.app.main as M


def _run(coro):
    return asyncio.run(coro)


class _Req:
    cookies: dict = {}
    headers: dict = {}
    scope: dict = {"type": "http", "headers": []}


def test_the_page_redirects_an_anonymous_visitor(monkeypatch):
    monkeypatch.setattr(M, "_get_user_from_request", lambda r: None)
    assert isinstance(_run(M.project_records_page("p1", _Req())), RedirectResponse)


def test_the_page_404s_for_a_project_the_user_does_not_own(monkeypatch):
    monkeypatch.setattr(M, "_get_user_from_request", lambda r: {"id": "u1"})
    monkeypatch.setattr(M, "projects_collection", lambda: type("C", (), {
        "find_one": staticmethod(lambda q: None)})())
    with pytest.raises(HTTPException) as e:
        _run(M.project_records_page("p1", _Req()))
    assert e.value.status_code == 404


def test_the_page_renders_the_project_it_was_asked_for(monkeypatch):
    monkeypatch.setattr(M, "_get_user_from_request", lambda r: {"id": "u1"})
    monkeypatch.setattr(M, "projects_collection", lambda: type("C", (), {
        "find_one": staticmethod(lambda q: {"id": "p1", "name": "Acme"})})())
    resp = _run(M.project_records_page("p1", _Req()))
    assert resp.template.name == "records.html"
    assert resp.context["project_id"] == "p1"
    assert resp.context["project_name"] == "Acme"


def test_the_template_surfaces_every_feature_it_exists_to_expose():
    html = (M.templates_dir / "records.html").read_text(encoding="utf-8")
    for needed in ("artefacts/freshness", "ropa/dfd.svg", "ropa.md",
                   "ropa/activities", "DPDPA domains", "Record of Processing Activities"):
        assert needed in html, f"records.html does not surface {needed!r}"


def test_the_template_keeps_the_not_legal_advice_framing():
    html = (M.templates_dir / "records.html").read_text(encoding="utf-8")
    assert "Not legal advice" in html
    assert "requires legal review" in html.lower()


def test_the_dashboard_links_to_the_records_page_so_it_is_discoverable():
    html = (M.templates_dir / "user_dashboard.html").read_text(encoding="utf-8")
    assert "/records" in html, "records page is unreachable from the dashboard"
