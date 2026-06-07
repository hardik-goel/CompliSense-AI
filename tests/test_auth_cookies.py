from fastapi import Response

from saas.app import auth as auth_module


def test_set_auth_cookie_uses_shared_cookie_domain(monkeypatch):
    response = Response()
    auth_module._set_auth_cookie(response, "token-123")

    cookie_header = response.headers["set-cookie"]
    assert "Domain=.complisenseai.com" in cookie_header
    assert "HttpOnly" in cookie_header
