"""Live integration tests for the Stack Exchange API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://api.stackexchange.com/2.3"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestSearchQuestions:
    """Tests for the Stack Exchange search endpoint."""

    def test_search_returns_items(self, session: requests.Session) -> None:
        """Searching for a common topic should return items array."""
        resp = session.get(
            f"{BASE_URL}/search",
            params={
                "order": "desc",
                "sort": "relevance",
                "intitle": "python",
                "site": "stackoverflow",
                "pagesize": 5,
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_search_items_have_title(self, session: requests.Session) -> None:
        """Each item in search results should have a title field."""
        resp = session.get(
            f"{BASE_URL}/search",
            params={
                "order": "desc",
                "sort": "relevance",
                "intitle": "python",
                "site": "stackoverflow",
                "pagesize": 1,
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        item = data["items"][0]
        assert "title" in item


class TestQuestionById:
    """Tests for fetching a specific question by ID."""

    def test_known_question(self, session: requests.Session) -> None:
        """Fetching a known question should return items with a title."""
        resp = session.get(
            f"{BASE_URL}/questions/292357",
            params={"site": "stackoverflow"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0
        question = data["items"][0]
        assert "title" in question

    def test_question_has_score(self, session: requests.Session) -> None:
        """A question response should include a score field."""
        resp = session.get(
            f"{BASE_URL}/questions/292357",
            params={"site": "stackoverflow"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        question = data["items"][0]
        assert "score" in question
