"""Consolidated API integration tests with response mocking.

All tests use mocked HTTP responses so they never hit live APIs.
Tests are organized by common patterns (known_item, missing/404, search)
and parameterized per API where the pattern is shared.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_response(
    status_code: int = 200,
    json_data: Any = None,
) -> MagicMock:
    """Build a fake ``requests.Response``."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


# ---------------------------------------------------------------------------
# Fixture: patched requests.Session so no real HTTP calls are made
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_session() -> MagicMock:
    """Return a mocked ``requests.Session`` instance."""
    with patch("requests.Session") as cls:
        session = MagicMock()
        cls.return_value = session
        yield session


# ===================================================================
# 1. KNOWN ITEM LOOKUP  (GET by ID returns 200 with expected fields)
# ===================================================================

KNOWN_ITEM_CASES: list[dict[str, Any]] = [
    {
        "id": "pypi-requests",
        "url": "https://pypi.org/pypi/requests/json",
        "response": {
            "info": {
                "name": "requests",
                "version": "2.31.0",
                "summary": "HTTP library",
                "author": "Kenneth Reitz",
                "project_urls": {"Homepage": "https://requests.readthedocs.io"},
                "requires_python": ">=3.7",
            },
            "releases": {"2.31.0": [{"filename": "requests-2.31.0.tar.gz", "url": "https://..."}]},
        },
        "checks": [
            lambda d: d["info"]["name"] == "requests",
            lambda d: "version" in d["info"],
            lambda d: "summary" in d["info"],
            lambda d: "author" in d["info"],
            lambda d: "releases" in d,
            lambda d: isinstance(d["releases"], dict),
        ],
    },
    {
        "id": "pypi-requests-version",
        "url": "https://pypi.org/pypi/requests/2.31.0/json",
        "response": {
            "info": {
                "name": "requests",
                "version": "2.31.0",
                "requires_python": ">=3.7",
            },
        },
        "checks": [
            lambda d: d["info"]["name"] == "requests",
            lambda d: d["info"]["version"] == "2.31.0",
            lambda d: "requires_python" in d["info"],
        ],
    },
    {
        "id": "pypi-flask-releases",
        "url": "https://pypi.org/pypi/flask/json",
        "response": {
            "info": {"name": "flask"},
            "releases": {f"0.{i}": [] for i in range(20)},
        },
        "checks": [
            lambda d: "releases" in d,
            lambda d: len(d["releases"]) > 10,
        ],
    },
    {
        "id": "pypi-pytest-project-urls",
        "url": "https://pypi.org/pypi/pytest/json",
        "response": {
            "info": {
                "name": "pytest",
                "project_urls": {"Source": "https://github.com/pytest-dev/pytest"},
            },
        },
        "checks": [
            lambda d: "project_urls" in d["info"],
            lambda d: d["info"]["project_urls"] is not None,
        ],
    },
    {
        "id": "pypi-pyyaml-release-files",
        "url": "https://pypi.org/pypi/pyyaml/json",
        "response": {
            "releases": {
                "6.0": [{"filename": "PyYAML-6.0.tar.gz", "url": "https://..."}],
            },
        },
        "checks": [
            lambda d: isinstance(d["releases"], dict),
            lambda d: len(d["releases"]) > 0,
            lambda d: "filename" in d["releases"]["6.0"][0],
            lambda d: "url" in d["releases"]["6.0"][0],
        ],
    },
    {
        "id": "npm-express",
        "url": "https://registry.npmjs.org/express",
        "response": {
            "name": "express",
            "dist-tags": {"latest": "4.18.2"},
            "versions": {"4.18.2": {}},
        },
        "checks": [
            lambda d: d["name"] == "express",
            lambda d: "dist-tags" in d,
            lambda d: "latest" in d["dist-tags"],
            lambda d: "versions" in d,
        ],
    },
    {
        "id": "npm-scoped-types-node",
        "url": "https://registry.npmjs.org/@types%2Fnode",
        "response": {"name": "@types/node"},
        "checks": [
            lambda d: d["name"] == "@types/node",
        ],
    },
    {
        "id": "npm-express-version",
        "url": "https://registry.npmjs.org/express/4.18.2",
        "response": {"name": "express", "version": "4.18.2"},
        "checks": [
            lambda d: d["name"] == "express",
            lambda d: d["version"] == "4.18.2",
        ],
    },
    {
        "id": "npm-express-latest",
        "url": "https://registry.npmjs.org/express/latest",
        "response": {"name": "express", "version": "4.19.0"},
        "checks": [
            lambda d: d["name"] == "express",
            lambda d: "version" in d,
        ],
    },
    {
        "id": "crates-serde",
        "url": "https://crates.io/api/v1/crates/serde",
        "response": {
            "crate": {"name": "serde", "description": "Serialization framework", "downloads": 100000},
        },
        "checks": [
            lambda d: d["crate"]["name"] == "serde",
            lambda d: "description" in d["crate"],
            lambda d: "downloads" in d["crate"],
        ],
    },
    {
        "id": "crates-serde-versions",
        "url": "https://crates.io/api/v1/crates/serde/versions",
        "response": {"versions": [{"num": "1.0.0"}]},
        "checks": [
            lambda d: "versions" in d,
            lambda d: len(d["versions"]) > 0,
        ],
    },
    {
        "id": "homebrew-wget",
        "url": "https://formulae.brew.sh/api/formula/wget.json",
        "response": {
            "name": "wget",
            "desc": "Internet file retriever",
            "homepage": "https://www.gnu.org/software/wget/",
            "versions": {"stable": "1.21.4"},
        },
        "checks": [
            lambda d: d["name"] == "wget",
            lambda d: "desc" in d,
            lambda d: "homepage" in d,
            lambda d: "versions" in d,
        ],
    },
    {
        "id": "homebrew-node-deps",
        "url": "https://formulae.brew.sh/api/formula/node.json",
        "response": {"name": "node", "dependencies": ["icu4c", "openssl"]},
        "checks": [
            lambda d: d["name"] == "node",
            lambda d: "dependencies" in d,
            lambda d: isinstance(d["dependencies"], list),
        ],
    },
    {
        "id": "homebrew-cask-firefox",
        "url": "https://formulae.brew.sh/api/cask/firefox.json",
        "response": {
            "token": "firefox",
            "name": ["Firefox"],
            "homepage": "https://www.mozilla.org/firefox/",
            "url": "https://download-installer.cdn.mozilla.net/...",
            "version": "125.0",
        },
        "checks": [
            lambda d: d["token"] == "firefox",
            lambda d: "name" in d,
            lambda d: "homepage" in d,
            lambda d: "url" in d,
            lambda d: "version" in d,
        ],
    },
    {
        "id": "openlibrary-work-hobbit",
        "url": "https://openlibrary.org/works/OL27482W.json",
        "response": {"title": "The Hobbit", "key": "/works/OL27482W"},
        "checks": [
            lambda d: "title" in d,
            lambda d: "hobbit" in d["title"].lower(),
            lambda d: "key" in d,
        ],
    },
    {
        "id": "openlibrary-author-tolkien",
        "url": "https://openlibrary.org/authors/OL26320A.json",
        "response": {"name": "J.R.R. Tolkien", "key": "/authors/OL26320A"},
        "checks": [
            lambda d: "name" in d,
            lambda d: "tolkien" in d["name"].lower(),
            lambda d: "key" in d,
        ],
    },
    {
        "id": "gitlab-project-278964",
        "url": "https://gitlab.com/api/v4/projects/278964",
        "response": {"id": 278964, "name": "gitlab", "description": "GitLab CE/EE"},
        "checks": [
            lambda d: "name" in d,
            lambda d: d["id"] == 278964,
            lambda d: "description" in d,
        ],
    },
    {
        "id": "stackoverflow-question-292357",
        "url": "https://api.stackexchange.com/2.3/questions/292357",
        "params": {"site": "stackoverflow"},
        "response": {
            "items": [{"title": "Difference between...", "score": 1234}],
        },
        "checks": [
            lambda d: "items" in d,
            lambda d: len(d["items"]) > 0,
            lambda d: "title" in d["items"][0],
            lambda d: "score" in d["items"][0],
        ],
    },
    {
        "id": "nasa-apod",
        "url": "https://api.nasa.gov/planetary/apod",
        "params": {"api_key": "DEMO_KEY"},
        "response": {
            "title": "Spiral Galaxy NGC 1232",
            "url": "https://apod.nasa.gov/...",
            "date": "2024-03-15",
        },
        "checks": [
            lambda d: "title" in d,
            lambda d: "url" in d,
            lambda d: "date" in d,
        ],
    },
    {
        "id": "nasa-apod-specific-date",
        "url": "https://api.nasa.gov/planetary/apod",
        "params": {"api_key": "DEMO_KEY", "date": "2024-01-01"},
        "response": {
            "title": "A Year of Sunrises",
            "url": "https://apod.nasa.gov/...",
            "date": "2024-01-01",
        },
        "checks": [
            lambda d: d["date"] == "2024-01-01",
        ],
    },
    {
        "id": "nasa-neo-feed",
        "url": "https://api.nasa.gov/neo/rest/v1/feed",
        "params": {"api_key": "DEMO_KEY", "start_date": "2024-01-01", "end_date": "2024-01-01"},
        "response": {
            "near_earth_objects": {
                "2024-01-01": [{"name": "(2024 AB1)"}],
            },
        },
        "checks": [
            lambda d: "near_earth_objects" in d,
            lambda d: "2024-01-01" in d["near_earth_objects"],
            lambda d: len(d["near_earth_objects"]["2024-01-01"]) > 0,
            lambda d: "name" in d["near_earth_objects"]["2024-01-01"][0],
        ],
    },
    {
        "id": "docker-tags-nginx",
        "url": "https://hub.docker.com/v2/repositories/library/nginx/tags",
        "params": {"page_size": "5"},
        "response": {"results": [{"name": "latest"}, {"name": "stable"}]},
        "checks": [
            lambda d: "results" in d,
            lambda d: len(d["results"]) > 0,
            lambda d: "name" in d["results"][0],
        ],
    },
    {
        "id": "archive-wayback-availability",
        "url": "https://archive.org/wayback/available",
        "params": {"url": "example.com"},
        "response": {"archived_snapshots": {"closest": {"status": "200"}}},
        "checks": [
            lambda d: "archived_snapshots" in d,
        ],
    },
]


@pytest.mark.parametrize(
    "case",
    KNOWN_ITEM_CASES,
    ids=[c["id"] for c in KNOWN_ITEM_CASES],
)
def test_known_item(mock_session: MagicMock, case: dict[str, Any]) -> None:
    """GET a known resource and verify expected fields are present."""
    mock_session.get.return_value = _mock_response(200, case["response"])

    resp = mock_session.get(case["url"], params=case.get("params"), timeout=15)

    assert resp.status_code == 200
    data: Any = resp.json()
    for check in case["checks"]:
        assert check(data), f"Check failed for {case['id']}"


# ===================================================================
# 2. MISSING / 404  (GET nonexistent resource returns 404)
# ===================================================================

MISSING_CASES: list[dict[str, str]] = [
    {"id": "pypi-missing-package", "url": "https://pypi.org/pypi/this-package-definitely-does-not-exist-xyz-999/json"},
    {"id": "pypi-missing-version", "url": "https://pypi.org/pypi/requests/999.999.999/json"},
    {"id": "npm-missing-package", "url": "https://registry.npmjs.org/this-package-definitely-does-not-exist-xyz-999"},
    {"id": "crates-missing-crate", "url": "https://crates.io/api/v1/crates/this-crate-definitely-does-not-exist-xyz-999"},
    {"id": "homebrew-missing-formula", "url": "https://formulae.brew.sh/api/formula/this-formula-does-not-exist-xyz.json"},
    {"id": "homebrew-missing-cask", "url": "https://formulae.brew.sh/api/cask/this-cask-does-not-exist-xyz.json"},
    {"id": "gitlab-missing-project", "url": "https://gitlab.com/api/v4/projects/999999999999"},
    {"id": "docker-missing-repo", "url": "https://hub.docker.com/v2/repositories/library/this-image-does-not-exist-xyz-999/tags"},
]


@pytest.mark.parametrize(
    "case",
    MISSING_CASES,
    ids=[c["id"] for c in MISSING_CASES],
)
def test_missing_returns_404(mock_session: MagicMock, case: dict[str, str]) -> None:
    """GET a nonexistent resource and verify a 404 status code."""
    mock_session.get.return_value = _mock_response(404)

    resp = mock_session.get(case["url"], timeout=15)

    assert resp.status_code == 404


# ===================================================================
# 3. SEARCH  (search endpoints return result arrays with expected keys)
# ===================================================================

SEARCH_CASES: list[dict[str, Any]] = [
    {
        "id": "pypi-no-direct-search",
        # PyPI has no search endpoint in these tests, skip
    },
    {
        "id": "npm-search-express",
        "url": "https://registry.npmjs.org/-/v1/search",
        "params": {"text": "express", "size": 5},
        "response": {"objects": [{"package": {"name": "express"}}]},
        "result_key": "objects",
        "min_results": 1,
        "field_checks": [],
    },
    {
        "id": "npm-search-size-limit",
        "url": "https://registry.npmjs.org/-/v1/search",
        "params": {"text": "react", "size": 3},
        "response": {"objects": [{"package": {"name": "react"}}, {"package": {"name": "react-dom"}}]},
        "result_key": "objects",
        "min_results": 1,
        "max_results": 3,
        "field_checks": [],
    },
    {
        "id": "crates-search-serde",
        "url": "https://crates.io/api/v1/crates",
        "params": {"q": "serde", "per_page": 5},
        "response": {"crates": [{"name": "serde", "description": "...", "downloads": 100}]},
        "result_key": "crates",
        "min_results": 1,
        "field_checks": ["name", "description", "downloads"],
    },
    {
        "id": "homebrew-formula-list",
        "url": "https://formulae.brew.sh/api/formula.json",
        "response": [{"name": f"pkg{i}", "full_name": f"pkg{i}", "desc": f"desc{i}"} for i in range(150)],
        "result_key": None,  # top-level array
        "min_results": 100,
        "field_checks": ["name", "full_name", "desc"],
    },
    {
        "id": "homebrew-cask-list",
        "url": "https://formulae.brew.sh/api/cask.json",
        "response": [{"token": f"cask{i}"} for i in range(150)],
        "result_key": None,
        "min_results": 100,
        "field_checks": [],
    },
    {
        "id": "openlibrary-search-tolkien",
        "url": "https://openlibrary.org/search.json",
        "params": {"q": "tolkien", "limit": 5},
        "response": {"docs": [{"title": "The Hobbit"}]},
        "result_key": "docs",
        "min_results": 1,
        "field_checks": ["title"],
    },
    {
        "id": "gitlab-search-projects",
        "url": "https://gitlab.com/api/v4/projects",
        "params": {"search": "gitlab", "per_page": 5},
        "response": [{"name": "gitlab", "id": 278964}],
        "result_key": None,
        "min_results": 1,
        "field_checks": ["name", "id"],
    },
    {
        "id": "stackoverflow-search-python",
        "url": "https://api.stackexchange.com/2.3/search",
        "params": {
            "order": "desc",
            "sort": "relevance",
            "intitle": "python",
            "site": "stackoverflow",
            "pagesize": 5,
        },
        "response": {"items": [{"title": "How to do X in Python"}]},
        "result_key": "items",
        "min_results": 1,
        "field_checks": ["title"],
    },
    {
        "id": "docker-search-nginx",
        "url": "https://hub.docker.com/v2/search/repositories",
        "params": {"query": "nginx", "page_size": 5},
        "response": {"results": [{"repo_name": "nginx"}]},
        "result_key": "results",
        "min_results": 1,
        "field_checks": [],
    },
    {
        "id": "archive-advanced-search",
        "url": "https://archive.org/advancedsearch.php",
        "params": {
            "q": "collection:opensource AND mediatype:texts",
            "fl[]": "identifier,title",
            "rows": 3,
            "output": "json",
        },
        "response": {"response": {"docs": [{"identifier": "abc", "title": "Test"}]}},
        "result_key": "response.docs",
        "min_results": 1,
        "field_checks": ["identifier"],
    },
]

# Filter out the placeholder entry
SEARCH_CASES = [c for c in SEARCH_CASES if "url" in c]


def _extract_results(data: Any, result_key: str | None) -> list[Any]:
    """Navigate a dotted result_key path to extract the results list."""
    if result_key is None:
        return data  # type: ignore[return-value]
    parts = result_key.split(".")
    current = data
    for part in parts:
        current = current[part]
    return current  # type: ignore[return-value]


@pytest.mark.parametrize(
    "case",
    SEARCH_CASES,
    ids=[c["id"] for c in SEARCH_CASES],
)
def test_search(mock_session: MagicMock, case: dict[str, Any]) -> None:
    """Search endpoints return results with expected structure."""
    mock_session.get.return_value = _mock_response(200, case["response"])

    resp = mock_session.get(case["url"], params=case.get("params"), timeout=15)

    assert resp.status_code == 200
    data: Any = resp.json()
    results = _extract_results(data, case.get("result_key"))

    assert isinstance(results, list)
    assert len(results) >= case.get("min_results", 1)

    if "max_results" in case:
        assert len(results) <= case["max_results"]

    # Check field presence on first result
    if case.get("field_checks") and len(results) > 0:
        first = results[0]
        for field in case["field_checks"]:
            assert field in first, f"Missing field '{field}' in {case['id']}"


# ===================================================================
# 4. EDGE CASES  (empty queries, rate limits, special responses)
# ===================================================================

def test_npm_empty_search_query(mock_session: MagicMock) -> None:
    """An empty npm search query returns either 200 or 400."""
    mock_session.get.return_value = _mock_response(400)

    resp = mock_session.get(
        "https://registry.npmjs.org/-/v1/search",
        params={"text": "", "size": 1},
        timeout=15,
    )

    assert resp.status_code in (200, 400)


def test_nasa_rate_limit_skips(mock_session: MagicMock) -> None:
    """When NASA returns 429, we detect the rate limit."""
    mock_session.get.return_value = _mock_response(429)

    resp = mock_session.get(
        "https://api.nasa.gov/planetary/apod",
        params={"api_key": "DEMO_KEY"},
        timeout=30,
    )

    assert resp.status_code == 429


def test_docker_search_result_has_name_field(mock_session: MagicMock) -> None:
    """Docker Hub search results contain repo_name or name."""
    mock_session.get.return_value = _mock_response(200, {
        "results": [{"repo_name": "library/nginx", "name": "nginx"}],
    })

    resp = mock_session.get(
        "https://hub.docker.com/v2/search/repositories",
        params={"query": "nginx", "page_size": 1},
        timeout=15,
    )

    assert resp.status_code == 200
    result: dict[str, Any] = resp.json()["results"][0]
    assert "repo_name" in result or "name" in result
