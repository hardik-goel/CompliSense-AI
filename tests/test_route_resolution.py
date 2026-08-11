"""Routes must resolve through the real router, not just exist as functions.

Every other API test calls the endpoint coroutine directly, which cannot catch a path being
shadowed by an earlier, more general route. FastAPI matches in registration order, so
``/artefacts/{art_id}`` registered before ``/artefacts/freshness`` silently swallows the
latter — the endpoint is perfectly correct and permanently unreachable.
"""

import pytest
from starlette.routing import Match

from saas.app.main import app


def _resolve(path: str, method: str = "GET"):
    scope = {"type": "http", "method": method, "path": path, "root_path": "",
             "headers": [], "query_string": b""}
    for route in app.routes:
        match, _child = route.matches(scope)
        if match == Match.FULL:
            return route
    return None


@pytest.mark.parametrize("path,expected", [
    ("/projects/p1/artefacts/freshness", "/projects/{project_id}/artefacts/freshness"),
    ("/projects/p1/artefacts/change-impact", "/projects/{project_id}/artefacts/change-impact"),
    ("/projects/p1/artefacts/regwatch-impact", "/projects/{project_id}/artefacts/regwatch-impact"),
    ("/projects/p1/artefacts/needed", "/projects/{project_id}/artefacts/needed"),
    ("/projects/p1/artefacts/list", "/projects/{project_id}/artefacts/list"),
    ("/projects/p1/artefacts/export.zip", "/projects/{project_id}/artefacts/export.zip"),
    ("/projects/p1/ropa", "/projects/{project_id}/ropa"),
    ("/projects/p1/ropa.md", "/projects/{project_id}/ropa.md"),
    ("/projects/p1/ropa/dfd.svg", "/projects/{project_id}/ropa/dfd.svg"),
])
def test_literal_paths_are_not_shadowed_by_a_wildcard_route(path, expected):
    route = _resolve(path)
    assert route is not None, f"{path} resolves to nothing"
    assert route.path == expected, f"{path} was shadowed by {route.path}"


def test_the_wildcard_artefact_route_still_works_for_a_real_artefact_id():
    route = _resolve("/projects/p1/artefacts/privacy_notice")
    assert route.path == "/projects/{project_id}/artefacts/{art_id}"


def test_no_two_routes_share_a_path_and_method():
    seen = set()
    for route in app.routes:
        for method in sorted(getattr(route, "methods", []) or []):
            key = (getattr(route, "path", ""), method)
            assert key not in seen, f"Duplicate route registered: {key}"
            seen.add(key)


# --- the records page must not collide with the ROPA JSON API ----------------------------

def test_the_records_page_resolves_to_the_page_not_the_api():
    route = _resolve("/projects/p1/records")
    assert route is not None and route.path == "/projects/{project_id}/records"


def test_the_ropa_json_api_is_not_shadowed_by_the_page():
    assert _resolve("/projects/p1/ropa").path == "/projects/{project_id}/ropa"
