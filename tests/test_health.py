import asyncio

from saas.app.main import health_check, simple_health_check


def test_health_endpoints_return_expected_payload():
    api_payload = asyncio.run(health_check())
    root_payload = asyncio.run(simple_health_check())

    assert api_payload["status"] == "healthy"
    assert root_payload == api_payload
    assert "service" in api_payload
