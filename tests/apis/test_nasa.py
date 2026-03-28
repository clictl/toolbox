"""Live integration tests for the NASA API.

NOTE: The DEMO_KEY is rate-limited to ~40 requests per hour per IP.
Tests will be skipped automatically if the rate limit is hit (HTTP 429).
"""

from __future__ import annotations

from typing import Any

import pytest
import requests


BASE_URL = "https://api.nasa.gov"
API_KEY = "DEMO_KEY"
TIMEOUT = 30


def _get_or_skip_rate_limit(
    session: requests.Session, url: str, params: dict[str, str]
) -> dict[str, Any]:
    """Perform a GET request and skip the test if rate-limited."""
    resp = session.get(url, params=params, timeout=TIMEOUT)
    if resp.status_code == 429:
        pytest.skip("NASA DEMO_KEY rate limit reached (HTTP 429)")
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    return data


@pytest.fixture(scope="module")
def session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


class TestApod:
    """Tests for the Astronomy Picture of the Day endpoint."""

    def test_apod_returns_expected_fields(self, session: requests.Session) -> None:
        """APOD should return a response with title, url, and date fields."""
        data = _get_or_skip_rate_limit(
            session,
            f"{BASE_URL}/planetary/apod",
            {"api_key": API_KEY},
        )
        assert "title" in data
        assert "url" in data
        assert "date" in data

    def test_apod_specific_date(self, session: requests.Session) -> None:
        """Requesting APOD for a specific date should return that date."""
        data = _get_or_skip_rate_limit(
            session,
            f"{BASE_URL}/planetary/apod",
            {"api_key": API_KEY, "date": "2024-01-01"},
        )
        assert data["date"] == "2024-01-01"


class TestNeoFeed:
    """Tests for the Near Earth Object feed endpoint."""

    def test_neo_feed_returns_objects(self, session: requests.Session) -> None:
        """NEO feed should return near_earth_objects keyed by date."""
        data = _get_or_skip_rate_limit(
            session,
            f"{BASE_URL}/neo/rest/v1/feed",
            {
                "api_key": API_KEY,
                "start_date": "2024-01-01",
                "end_date": "2024-01-01",
            },
        )
        assert "near_earth_objects" in data
        assert "2024-01-01" in data["near_earth_objects"]
        objects = data["near_earth_objects"]["2024-01-01"]
        assert len(objects) > 0
        assert "name" in objects[0]
