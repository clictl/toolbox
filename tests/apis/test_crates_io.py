"""Live integration tests for the crates.io API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://crates.io/api/v1"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with required headers."""
    s = requests.Session()
    s.headers.update({
        "Accept": "application/json",
        "User-Agent": "clictl-tests/1.0",
    })
    return s


class TestCrateSearch:
    """Tests for the crates.io search endpoint."""

    def test_search_returns_results(self, session: requests.Session) -> None:
        """Searching for a common crate should return results."""
        resp = session.get(
            f"{BASE_URL}/crates",
            params={"q": "serde", "per_page": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "crates" in data
        assert len(data["crates"]) > 0

    def test_search_crate_has_expected_fields(self, session: requests.Session) -> None:
        """Each crate in search results should have standard fields."""
        resp = session.get(
            f"{BASE_URL}/crates",
            params={"q": "tokio", "per_page": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        crate = data["crates"][0]
        assert "name" in crate
        assert "description" in crate
        assert "downloads" in crate


class TestCrateInfo:
    """Tests for the crates.io crate info endpoint."""

    def test_known_crate(self, session: requests.Session) -> None:
        """Fetching a well-known crate should return valid metadata."""
        resp = session.get(f"{BASE_URL}/crates/serde", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        crate = data["crate"]
        assert crate["name"] == "serde"
        assert "description" in crate
        assert "downloads" in crate

    def test_crate_has_versions(self, session: requests.Session) -> None:
        """A well-known crate should have version history."""
        resp = session.get(f"{BASE_URL}/crates/serde/versions", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "versions" in data
        assert len(data["versions"]) > 0

    def test_nonexistent_crate(self, session: requests.Session) -> None:
        """A nonexistent crate should return 404."""
        resp = session.get(
            f"{BASE_URL}/crates/this-crate-definitely-does-not-exist-xyz-999",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404
