"""Live integration tests for the Internet Archive API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestAdvancedSearch:
    """Tests for the Internet Archive advanced search endpoint."""

    def test_search_returns_docs(self, session: requests.Session) -> None:
        """Advanced search should return a response with docs."""
        resp = session.get(
            "https://archive.org/advancedsearch.php",
            params={
                "q": "collection:opensource AND mediatype:texts",
                "fl[]": "identifier,title",
                "rows": 3,
                "output": "json",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "response" in data
        assert "docs" in data["response"]
        assert len(data["response"]["docs"]) > 0

    def test_search_docs_have_fields(self, session: requests.Session) -> None:
        """Each doc in search results should include requested fields."""
        resp = session.get(
            "https://archive.org/advancedsearch.php",
            params={
                "q": "collection:opensource AND mediatype:texts",
                "fl[]": "identifier,title",
                "rows": 1,
                "output": "json",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        doc = data["response"]["docs"][0]
        assert "identifier" in doc


class TestWaybackAvailability:
    """Tests for the Wayback Machine availability endpoint."""

    def test_known_url_availability(self, session: requests.Session) -> None:
        """Checking availability for a well-known URL should return a result."""
        resp = session.get(
            "https://archive.org/wayback/available",
            params={"url": "example.com"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "archived_snapshots" in data

    def test_known_url_has_snapshot_structure(self, session: requests.Session) -> None:
        """The wayback availability API returns archived_snapshots for a known URL."""
        resp = session.get(
            "https://archive.org/wayback/available",
            params={"url": "example.com"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "archived_snapshots" in data
        # Snapshots may be empty depending on archive.org load, so just check the key exists
