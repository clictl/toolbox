"""Live integration tests for the PyPI API."""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://pypi.org"
TIMEOUT = 15


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestPackageInfo:
    """Tests for the PyPI package info endpoint."""

    def test_known_package(self, session: requests.Session) -> None:
        """Fetching a well-known package should return valid metadata."""
        resp = session.get(f"{BASE_URL}/pypi/requests/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        info: dict[str, Any] = data["info"]
        assert info["name"] == "requests"
        assert "version" in info
        assert "summary" in info
        assert "author" in info

    def test_package_has_releases(self, session: requests.Session) -> None:
        """A well-known package should have release history."""
        resp = session.get(f"{BASE_URL}/pypi/flask/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        assert "releases" in data
        assert len(data["releases"]) > 10, "Expected many Flask releases"

    def test_package_project_urls(self, session: requests.Session) -> None:
        """Package metadata should include project URLs when available."""
        resp = session.get(f"{BASE_URL}/pypi/pytest/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        info: dict[str, Any] = data["info"]
        assert "project_urls" in info
        assert info["project_urls"] is not None

    def test_nonexistent_package(self, session: requests.Session) -> None:
        """A nonexistent package should return 404."""
        resp = session.get(
            f"{BASE_URL}/pypi/this-package-definitely-does-not-exist-xyz-999/json",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404


class TestPackageVersion:
    """Tests for the PyPI package version endpoint."""

    def test_specific_version(self, session: requests.Session) -> None:
        """Fetching a specific version should return matching metadata."""
        resp = session.get(f"{BASE_URL}/pypi/requests/2.31.0/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        info: dict[str, Any] = data["info"]
        assert info["name"] == "requests"
        assert info["version"] == "2.31.0"

    def test_version_has_requires_python(self, session: requests.Session) -> None:
        """A modern package version should specify required Python version."""
        resp = session.get(f"{BASE_URL}/pypi/requests/2.31.0/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        info: dict[str, Any] = data["info"]
        assert "requires_python" in info

    def test_nonexistent_version(self, session: requests.Session) -> None:
        """A nonexistent version should return 404."""
        resp = session.get(
            f"{BASE_URL}/pypi/requests/999.999.999/json",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 404


class TestPackageReleases:
    """Tests for extracting release data from the package endpoint."""

    def test_releases_are_dict(self, session: requests.Session) -> None:
        """Releases should be a dictionary keyed by version string."""
        resp = session.get(f"{BASE_URL}/pypi/pyyaml/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        releases = data["releases"]
        assert isinstance(releases, dict)
        assert len(releases) > 0

    def test_release_contains_files(self, session: requests.Session) -> None:
        """Each release entry should contain a list of distribution files."""
        resp = session.get(f"{BASE_URL}/pypi/pyyaml/json", timeout=TIMEOUT)
        assert resp.status_code == 200
        data: dict[str, Any] = resp.json()
        releases = data["releases"]
        non_empty_releases = {v: files for v, files in releases.items() if files}
        assert len(non_empty_releases) > 0, "Expected at least one release with files"
        first_version = next(iter(non_empty_releases))
        first_file = non_empty_releases[first_version][0]
        assert "filename" in first_file
        assert "url" in first_file
