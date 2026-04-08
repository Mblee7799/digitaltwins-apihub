"""Tests for the Hub API endpoints."""

import pytest
from fastapi.testclient import TestClient

from hub.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["tools_loaded"] >= 4


def test_list_tools(client):
    r = client.get("/api/v1/tools")
    assert r.status_code == 200
    tools = r.json()
    tool_ids = [t["id"] for t in tools]
    assert "buffer" in tool_ids
    assert "centroid" in tool_ids
    assert "ping" in tool_ids


def test_get_tool(client):
    r = client.get("/api/v1/tools/buffer")
    assert r.status_code == 200
    assert r.json()["id"] == "buffer"


def test_get_tool_not_found(client):
    r = client.get("/api/v1/tools/nonexistent")
    assert r.status_code == 404


def test_run_buffer(client):
    r = client.post(
        "/api/v1/tools/buffer/run",
        json={
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-118.24, 34.05]},
                        "properties": {"name": "Downtown LA"},
                    }
                ],
            },
            "parameters": {"distance_m": 500},
        },
    )
    assert r.status_code == 200
    data = r.json()

    # Execution envelope
    assert data["execution"]["tool_id"] == "buffer"
    assert data["execution"]["status"] == "success"
    assert data["execution"]["feature_count"] == 1

    # Pure GeoJSON result
    fc = data["result"]
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["features"][0]["geometry"]["type"] == "Polygon"
    assert fc["features"][0]["properties"]["buffer_distance_m"] == 500


def test_run_centroid(client):
    r = client.post(
        "/api/v1/tools/centroid/run",
        json={
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-118.3, 34.0],
                                    [-118.2, 34.0],
                                    [-118.2, 34.1],
                                    [-118.3, 34.1],
                                    [-118.3, 34.0],
                                ]
                            ],
                        },
                        "properties": {"name": "Test Polygon"},
                    }
                ],
            },
            "parameters": {},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["execution"]["tool_id"] == "centroid"
    assert data["result"]["features"][0]["geometry"]["type"] == "Point"


def test_run_ping(client):
    r = client.post(
        "/api/v1/tools/ping/run",
        json={"parameters": {}},
    )
    assert r.status_code == 200
    data = r.json()

    assert data["execution"]["tool_id"] == "ping"
    assert data["execution"]["status"] == "success"
    assert data["execution"]["feature_count"] == 2

    fc = data["result"]
    features = fc["features"]

    # Feature 1: DTLA point
    dtla = features[0]
    assert dtla["geometry"]["type"] == "Point"
    assert dtla["properties"]["message"] == "pong"
    assert dtla["properties"]["name"] == "Downtown Los Angeles"
    coords = dtla["geometry"]["coordinates"]
    assert abs(coords[0] - (-118.2437)) < 0.01
    assert abs(coords[1] - 34.0522) < 0.01

    # Feature 2: CONUS bounding box
    conus = features[1]
    assert conus["geometry"]["type"] == "Polygon"
    assert conus["properties"]["name"] == "Contiguous United States"
    assert conus["properties"]["message"] == "pong"


def test_ping_manifest_no_geometry_required(client):
    r = client.get("/api/v1/tools/ping")
    assert r.status_code == 200
    manifest = r.json()
    assert manifest["geometry_input"]["required"] is False


def test_manifest_has_ui_hints(client):
    r = client.get("/api/v1/tools/buffer")
    assert r.status_code == 200
    manifest = r.json()

    # Check parameter UI hints
    distance_param = next(p for p in manifest["parameters"] if p["name"] == "distance_m")
    assert distance_param["widget"] == "slider"
    assert distance_param["unit"] == "meters"
    assert distance_param["min"] == 0
    assert distance_param["max"] == 50000
    assert distance_param["step"] == 100
    assert distance_param["group"] == "analysis"

    # Check output hints
    assert manifest["output_hints"]["suggested_display"] == "choropleth"

    # Check geometry input
    assert manifest["geometry_input"]["required"] is True
    assert "point" in manifest["geometry_input"]["draw_modes"]

    # Check execution config
    assert manifest["execution"]["mode"] == "sync"

    # Check chaining tags
    assert "polygon" in manifest["output_tags"]
    assert "analysis" in manifest["output_tags"]


def test_run_env_check_metrics_only(client):
    """Test a tool that returns metrics + tables but no geometry."""
    r = client.post(
        "/api/v1/tools/env-check/run",
        json={
            "parameters": {"latitude": 34.0522, "longitude": -118.2437},
        },
    )
    assert r.status_code == 200
    data = r.json()

    # Execution envelope
    assert data["execution"]["tool_id"] == "env-check"
    assert data["execution"]["status"] == "success"
    assert data["execution"]["feature_count"] == 0  # no geometry

    # No GeoJSON result
    assert data["result"] is None

    # Metrics returned
    assert "air_quality" in data["metrics"]
    assert "aqi" in data["metrics"]["air_quality"]
    assert "temperature" in data["metrics"]
    assert "vegetation" in data["metrics"]

    # Tables returned
    assert len(data["tables"]) == 5
    assert data["tables"][0]["metric"] == "Air Quality Index"
    assert "unit" in data["tables"][0]

    # Warnings present
    assert len(data["warnings"]) > 0


def test_env_check_manifest_declares_secrets(client):
    """Test that the manifest declares required API secrets."""
    r = client.get("/api/v1/tools/env-check")
    assert r.status_code == 200
    manifest = r.json()

    assert "GOOGLE_MAPS_KEY" in manifest["requirements"]["secrets"]
    assert "google_air_quality" in manifest["requirements"]["apis"]
    assert manifest["output_hints"]["suggested_display"] == "dashboard"
    assert manifest["geometry_input"]["required"] is False
    assert "click" in manifest["geometry_input"]["draw_modes"]


def test_run_env_check_from_geometry(client):
    """Test that env-check accepts a clicked point instead of lat/lng params."""
    r = client.post(
        "/api/v1/tools/env-check/run",
        json={
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-118.24, 34.05]},
                        "properties": {},
                    }
                ],
            },
            "parameters": {},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["metrics"]["location"]["latitude"] == 34.05
    assert data["metrics"]["location"]["longitude"] == -118.24


def test_run_missing_params(client):
    r = client.post(
        "/api/v1/tools/buffer/run",
        json={
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [0, 0]},
                        "properties": {},
                    }
                ],
            },
            "parameters": {},
        },
    )
    assert r.status_code == 422
