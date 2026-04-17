"""Tests for the Nearest Feature Finder tool."""

import pytest
from tools.nearest_feature.tool import NearestFeatureTool
from sdk.types import ToolInput
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Point


@pytest.fixture
def tool():
    return NearestFeatureTool()


@pytest.fixture
def query_and_targets():
    """One query point and three target features."""
    return FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.25, 34.05]),
                properties={"name": "Query Location"},
            ),
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.26, 34.06]),
                properties={"name": "Hospital A", "_is_target": True, "type": "hospital"},
            ),
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.24, 34.04]),
                properties={"name": "Hospital B", "_is_target": True, "type": "hospital"},
            ),
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.30, 34.10]),
                properties={"name": "Hospital C", "_is_target": True, "type": "hospital"},
            ),
        ],
    )


@pytest.fixture
def multiple_queries():
    """Multiple query points with targets."""
    return FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.25, 34.05]),
                properties={"name": "Location 1"},
            ),
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.20, 34.00]),
                properties={"name": "Location 2"},
            ),
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.26, 34.06]),
                properties={"name": "Park A", "_is_target": True},
            ),
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.24, 34.04]),
                properties={"name": "Park B", "_is_target": True},
            ),
        ],
    )


def test_manifest(tool):
    manifest = tool.manifest()
    assert manifest.id == "nearest-feature"
    assert manifest.name == "Nearest Feature Finder"
    assert manifest.author == "MLee7"
    assert "proximity" in manifest.tags
    assert len(manifest.parameters) == 7


def test_find_single_nearest(tool, query_and_targets):
    tool_input = ToolInput(geojson=query_and_targets, parameters={"k_nearest": 1})
    result = tool.execute(tool_input)

    assert result.result is not None
    points = [f for f in result.result.features if f.geometry.type == "Point"]
    assert len(points) >= 1
    
    nearest_point = points[0]
    props = nearest_point.properties
    assert "nearest_name" in props
    assert "distance_m" in props
    assert props["rank"] == 1


def test_find_k_nearest(tool, query_and_targets):
    tool_input = ToolInput(geojson=query_and_targets, parameters={"k_nearest": 3})
    result = tool.execute(tool_input)

    points = [f for f in result.result.features if f.geometry.type == "Point"]
    assert len(points) == 3
    
    ranks = [p.properties["rank"] for p in points]
    assert ranks == [1, 2, 3]
    
    distances = [p.properties["distance_m"] for p in points]
    assert distances == sorted(distances)


def test_draw_connection_lines(tool, query_and_targets):
    tool_input = ToolInput(
        geojson=query_and_targets, parameters={"k_nearest": 2, "draw_lines": True}
    )
    result = tool.execute(tool_input)

    lines = [f for f in result.result.features if f.geometry.type == "LineString"]
    assert len(lines) == 2
    
    for line in lines:
        props = line.properties
        assert "connection_type" in props
        assert props["connection_type"] == "nearest_path"
        assert "from" in props
        assert "to" in props
        assert "distance_m" in props


def test_no_lines_when_disabled(tool, query_and_targets):
    tool_input = ToolInput(
        geojson=query_and_targets, parameters={"k_nearest": 2, "draw_lines": False}
    )
    result = tool.execute(tool_input)

    lines = [f for f in result.result.features if f.geometry.type == "LineString"]
    assert len(lines) == 0


def test_max_distance_filter(tool, query_and_targets):
    tool_input = ToolInput(
        geojson=query_and_targets, parameters={"k_nearest": 3, "max_distance_m": 5000}
    )
    result = tool.execute(tool_input)

    points = [f for f in result.result.features if f.geometry.type == "Point"]
    
    for point in points:
        if "distance_m" in point.properties:
            assert point.properties["distance_m"] <= 5000


def test_metric_units(tool, query_and_targets):
    tool_input = ToolInput(
        geojson=query_and_targets,
        parameters={"k_nearest": 1, "include_metric": True, "include_imperial": False},
    )
    result = tool.execute(tool_input)

    points = [f for f in result.result.features if f.geometry.type == "Point"]
    props = points[0].properties
    assert "distance_km" in props
    assert "distance_miles" not in props
    assert "distance_feet" not in props


def test_imperial_units(tool, query_and_targets):
    tool_input = ToolInput(
        geojson=query_and_targets,
        parameters={"k_nearest": 1, "include_metric": False, "include_imperial": True},
    )
    result = tool.execute(tool_input)

    points = [f for f in result.result.features if f.geometry.type == "Point"]
    props = points[0].properties
    assert "distance_miles" in props
    assert "distance_feet" in props
    assert "distance_km" not in props


def test_multiple_query_points(tool, multiple_queries):
    tool_input = ToolInput(geojson=multiple_queries, parameters={"k_nearest": 1})
    result = tool.execute(tool_input)

    points = [f for f in result.result.features if f.geometry.type == "Point"]
    assert len(points) >= 2


def test_preserves_target_properties(tool, query_and_targets):
    tool_input = ToolInput(geojson=query_and_targets, parameters={"k_nearest": 1})
    result = tool.execute(tool_input)

    points = [f for f in result.result.features if f.geometry.type == "Point"]
    props = points[0].properties
    assert "nearest_type" in props
    assert props["nearest_type"] == "hospital"


def test_empty_input(tool):
    empty_fc = FeatureCollection(type="FeatureCollection", features=[])
    tool_input = ToolInput(geojson=empty_fc, parameters={})

    with pytest.raises(ValueError, match="No query points provided"):
        tool.execute(tool_input)


def test_no_targets(tool):
    only_query = FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.25, 34.05]),
                properties={"name": "Query"},
            )
        ],
    )
    tool_input = ToolInput(geojson=only_query, parameters={})

    with pytest.raises(ValueError, match="No target features found"):
        tool.execute(tool_input)


def test_warnings(tool, query_and_targets):
    tool_input = ToolInput(geojson=query_and_targets, parameters={})
    result = tool.execute(tool_input)

    assert result.warnings is not None
    assert len(result.warnings) > 0
    assert any("approximation" in w.lower() for w in result.warnings)
