"""Live integration tests for the Homebrew Formulae API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://formulae.brew.sh/api"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestFormulaList:
    """Tests for the formula listing endpoint."""

    def test_formula_list_returns_array(self, session: requests.Session) -> None:
        """The formula list endpoint should return a JSON array."""
        resp = session.get(f"{BASE_URL}/formula.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: list[dict[str, Any]] = resp.json()
        assert isinstance(data, list)
        assert len(data) > 100, "Expected many formulae in the list"

    def test_formula_list_has_expected_fields(self, session: requests.Session) -> None:
        """Each formula in the list should have basic metadata fields."""
        resp = session.get(f"{BASE_URL}/formula.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: list[dict[str, Any]] = resp.json()
        first = data[0]
        assert "name" in first
        assert "full_name" in first
        assert "desc" in first


class TestFormulaInfo:
    """Tests for the individual formula info endpoint."""

    def test_known_formula(self, session: requests.Session) -> None:
        """Fetching a well-known formula should return valid metadata."""
        resp = session.get(f"{BASE_URL}/formula/wget.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["name"] == "wget"
        assert "desc" in data
        assert "homepage" in data
        assert "versions" in data

    def test_formula_with_dependencies(self, session: requests.Session) -> None:
        """A formula with known dependencies should list them."""
        resp = session.get(f"{BASE_URL}/formula/node.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["name"] == "node"
        assert "dependencies" in data
        assert isinstance(data["dependencies"], list)

    def test_nonexistent_formula(self, session: requests.Session) -> None:
        """A nonexistent formula should return 404."""
        resp = session.get(
            f"{BASE_URL}/formula/this-formula-does-not-exist-xyz.json",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404


class TestCaskList:
    """Tests for the cask listing endpoint."""

    def test_cask_list_returns_array(self, session: requests.Session) -> None:
        """The cask list endpoint should return a JSON array."""
        resp = session.get(f"{BASE_URL}/cask.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: list[dict[str, Any]] = resp.json()
        assert isinstance(data, list)
        assert len(data) > 100, "Expected many casks in the list"


class TestCaskInfo:
    """Tests for the individual cask info endpoint."""

    def test_known_cask(self, session: requests.Session) -> None:
        """Fetching a well-known cask should return valid metadata."""
        resp = session.get(f"{BASE_URL}/cask/firefox.json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert data["token"] == "firefox"
        assert "name" in data
        assert "homepage" in data
        assert "url" in data
        assert "version" in data

    def test_nonexistent_cask(self, session: requests.Session) -> None:
        """A nonexistent cask should return 404."""
        resp = session.get(
            f"{BASE_URL}/cask/this-cask-does-not-exist-xyz.json",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404
