"""
Tests for the CosmiDex FastAPI layer, run against the live Postgres instance.
"""

# Import dependencies
import os
import sys

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "cosmidex_api"))

from main import app  # noqa: E402

load_dotenv()

API_KEY = os.environ["API_KEY"]
AUTH_HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_planets_requires_api_key(client):
    response = client.get("/planets")
    assert response.status_code == 401


def test_planets_rejects_bad_api_key(client):
    response = client.get("/planets", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_get_planets(client):
    response = client.get("/planets", headers=AUTH_HEADERS)
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) > 0
    assert "planet_name" in rows[0]
    assert "esi_score" in rows[0]


def test_get_planets_limit(client):
    response = client.get("/planets?limit=5", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) <= 5


def test_get_planets_esi_filter(client):
    response = client.get("/planets?min_esi=0.5&max_esi=1.0", headers=AUTH_HEADERS)
    assert response.status_code == 200
    for row in response.json():
        assert row["esi_score"] is None or 0.5 <= row["esi_score"] <= 1.0


def test_get_planets_by_tier(client):
    response = client.get("/planets/tier/Tier 1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    for row in response.json():
        assert row["habitability_tier"] == "Tier 1"


def test_search_planets(client):
    response = client.get("/planets/search/TRAPPIST", headers=AUTH_HEADERS)
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) > 0
    for row in rows:
        assert "TRAPPIST" in row["planet_name"].upper()


def test_get_habitable_planets(client):
    response = client.get("/planets/habitable/list", headers=AUTH_HEADERS)
    assert response.status_code == 200
    for row in response.json():
        assert row["habitability_tier"] != "Non-Habitable"


def test_get_latest_audit(client):
    response = client.get("/audit/latest", headers=AUTH_HEADERS)
    assert response.status_code == 200
    row = response.json()
    assert row["pipeline_name"] == "nasa_exoplanets"
    assert "planet_count" in row


def test_get_single_planet(client):
    planets = client.get("/planets?limit=1", headers=AUTH_HEADERS).json()
    planet_name = planets[0]["planet_name"]

    response = client.get(f"/planets/{planet_name}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    row = response.json()
    assert row["planet_name"] == planet_name
    assert "esi_score" in row


def test_get_single_planet_not_found(client):
    response = client.get("/planets/Definitely Not A Real Planet", headers=AUTH_HEADERS)
    assert response.status_code == 404
