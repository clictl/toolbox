"""Live integration tests for the Open Library API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://openlibrary.org"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestSearch:
    """Tests for the Open Library search endpoint."""

    def test_search_returns_docs(self, session: requests.Session) -> None:
        """Searching for a known author should return docs array."""
        resp = session.get(
            f"{BASE_URL}/search.json",
            params={"q": "tolkien", "limit": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "docs" in data
        assert len(data["docs"]) > 0

    def test_search_docs_have_title(self, session: requests.Session) -> None:
        """Search results should include a title field."""
        resp = session.get(
            f"{BASE_URL}/search.json",
            params={"q": "tolkien", "limit": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        doc = data["docs"][0]
        assert "title" in doc


class TestWorkInfo:
    """Tests for the Open Library works endpoint."""

    def test_known_work(self, session: requests.Session) -> None:
        """Fetching The Hobbit by work ID should return its title."""
        resp = session.get(f"{BASE_URL}/works/OL27482W.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "title" in data
        assert "hobbit" in data["title"].lower()

    def test_work_has_key(self, session: requests.Session) -> None:
        """A work should include its own key in the response."""
        resp = session.get(f"{BASE_URL}/works/OL27482W.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "key" in data


class TestAuthorInfo:
    """Tests for the Open Library authors endpoint."""

    def test_known_author(self, session: requests.Session) -> None:
        """Fetching J.R.R. Tolkien by author ID should return name."""
        resp = session.get(f"{BASE_URL}/authors/OL26320A.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "name" in data
        assert "tolkien" in data["name"].lower()

    def test_author_has_key(self, session: requests.Session) -> None:
        """An author response should include its own key."""
        resp = session.get(f"{BASE_URL}/authors/OL26320A.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "key" in data
