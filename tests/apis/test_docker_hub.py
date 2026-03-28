"""Live integration tests for the Docker Hub API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://hub.docker.com/v2"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestDockerSearch:
    """Tests for the Docker Hub search endpoint."""

    def test_search_returns_results(self, session: requests.Session) -> None:
        """Searching for a common image should return results."""
        resp = session.get(
            f"{BASE_URL}/search/repositories",
            params={"query": "nginx", "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_search_result_has_name(self, session: requests.Session) -> None:
        """Each search result should contain a name field."""
        resp = session.get(
            f"{BASE_URL}/search/repositories",
            params={"query": "nginx", "page_size": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        result = data["results"][0]
        assert "repo_name" in result or "name" in result


class TestDockerTags:
    """Tests for the Docker Hub tags endpoint."""

    def test_tags_returns_results(self, session: requests.Session) -> None:
        """Fetching tags for the official nginx image should return results."""
        resp = session.get(
            f"{BASE_URL}/repositories/library/nginx/tags",
            params={"page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_tag_has_name(self, session: requests.Session) -> None:
        """Each tag entry should have a name field."""
        resp = session.get(
            f"{BASE_URL}/repositories/library/nginx/tags",
            params={"page_size": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        tag = data["results"][0]
        assert "name" in tag

    def test_nonexistent_repo_tags(self, session: requests.Session) -> None:
        """Tags for a nonexistent repository should return 404."""
        resp = session.get(
            f"{BASE_URL}/repositories/library/this-image-does-not-exist-xyz-999/tags",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404
