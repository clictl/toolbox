"""Live integration tests for pkg.go.dev website."""

from __future__ import annotations

import pytest
import requests


BASE_URL = "https://pkg.go.dev"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with a browser-like User-Agent."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "clictl-tests/1.0",
        "Accept": "text/html,application/xhtml+xml",
    })
    return s


class TestGoDocsSearch:
    """Tests for pkg.go.dev search functionality."""

    def test_search_returns_ok(self, session: requests.Session) -> None:
        """Searching for a common package should return HTTP 200."""
        resp = session.get(
            f"{BASE_URL}/search",
            params={"q": "http"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200

    def test_search_returns_html(self, session: requests.Session) -> None:
        """Search results should be returned as HTML content."""
        resp = session.get(
            f"{BASE_URL}/search",
            params={"q": "http"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        content_type = resp.headers.get("Content-Type", "")
        assert "text/html" in content_type

    def test_search_content_not_empty(self, session: requests.Session) -> None:
        """Search response body should not be empty."""
        resp = session.get(
            f"{BASE_URL}/search",
            params={"q": "json"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        assert len(resp.text) > 0


class TestGoDocsPackagePage:
    """Tests for pkg.go.dev package detail pages."""

    def test_known_package_returns_ok(self, session: requests.Session) -> None:
        """Fetching a well-known package page should return HTTP 200."""
        resp = session.get(f"{BASE_URL}/net/http", timeout=TIMEOUT)
        assert resp.status_code == 200

    def test_known_package_contains_name(self, session: requests.Session) -> None:
        """The package page should contain the package name in the body."""
        resp = session.get(f"{BASE_URL}/net/http", timeout=TIMEOUT)
        assert resp.status_code == 200
        assert "http" in resp.text.lower()
