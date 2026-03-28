"""Live integration tests for the GitLab public API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://gitlab.com/api/v4"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestProjectSearch:
    """Tests for the GitLab public project search endpoint."""

    def test_search_returns_projects(self, session: requests.Session) -> None:
        """Searching for public projects should return an array."""
        resp = session.get(
            f"{BASE_URL}/projects",
            params={"search": "gitlab", "per_page": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: list[dict[str, Any]] = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_search_result_has_name(self, session: requests.Session) -> None:
        """Each project in search results should have a name field."""
        resp = session.get(
            f"{BASE_URL}/projects",
            params={"search": "gitlab", "per_page": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: list[dict[str, Any]] = resp.json()
        project = data[0]
        assert "name" in project
        assert "id" in project


class TestProjectById:
    """Tests for fetching a specific GitLab project by ID."""

    def test_known_project(self, session: requests.Session) -> None:
        """Fetching the gitlab-org/gitlab project should return its name."""
        resp = session.get(f"{BASE_URL}/projects/278964", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "name" in data
        assert data["id"] == 278964

    def test_project_has_description(self, session: requests.Session) -> None:
        """A known project should have a description field."""
        resp = session.get(f"{BASE_URL}/projects/278964", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "description" in data

    def test_nonexistent_project(self, session: requests.Session) -> None:
        """A nonexistent project ID should return 404."""
        resp = session.get(f"{BASE_URL}/projects/999999999999", timeout=TIMEOUT)
        assert resp.status_code == 404
