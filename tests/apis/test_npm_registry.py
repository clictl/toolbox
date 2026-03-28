"""Live integration tests for the npm registry API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://registry.npmjs.org"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestNpmSearch:
    """Tests for the npm search endpoint."""

    def test_search_returns_results(self, session: requests.Session) -> None:
        """Searching for a common term should return results."""
        resp = session.get(
            f"{BASE_URL}/-/v1/search",
            params={"text": "express", "size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "objects" in data
        assert len(data["objects"]) > 0

    def test_search_respects_size(self, session: requests.Session) -> None:
        """The size parameter should limit the number of results."""
        resp = session.get(
            f"{BASE_URL}/-/v1/search",
            params={"text": "react", "size": 3},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert len(data["objects"]) <= 3

    def test_search_empty_query(self, session: requests.Session) -> None:
        """An empty search query returns 400 (text is required)."""
        resp = session.get(
            f"{BASE_URL}/-/v1/search",
            params={"text": "", "size": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 400)


class TestNpmPackageInfo:
    """Tests for the npm package info endpoint."""

    def test_known_package(self, session: requests.Session) -> None:
        """Fetching a well-known package should return valid metadata."""
        resp = session.get(f"{BASE_URL}/express", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["name"] == "express"
        assert "dist-tags" in data
        assert "latest" in data["dist-tags"]
        assert "versions" in data

    def test_scoped_package(self, session: requests.Session) -> None:
        """Scoped packages should be retrievable with URL encoding."""
        resp = session.get(f"{BASE_URL}/@types%2Fnode", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["name"] == "@types/node"

    def test_nonexistent_package(self, session: requests.Session) -> None:
        """A nonexistent package should return 404."""
        resp = session.get(
            f"{BASE_URL}/this-package-definitely-does-not-exist-xyz-999",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404


class TestNpmPackageVersion:
    """Tests for the npm package version endpoint."""

    def test_specific_version(self, session: requests.Session) -> None:
        """Fetching a specific version should return matching metadata."""
        resp = session.get(f"{BASE_URL}/express/4.18.2", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["name"] == "express"
        assert data["version"] == "4.18.2"

    def test_latest_tag(self, session: requests.Session) -> None:
        """Fetching 'latest' should resolve to a valid version."""
        resp = session.get(f"{BASE_URL}/express/latest", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["name"] == "express"
        assert "version" in data
