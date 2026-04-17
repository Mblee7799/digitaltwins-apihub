"""Tests for the Area & Perimeter Calculator tool."""

import pytest
from tools.area_perimeter.tool import AreaPerimeterTool
from sdk.types import ToolInput
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon


@pytest.fixture
def tool():
    return AreaPerimeterTool()


@pytest.fixture
def square_polygon():
    return FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                geometry=Polygon(
                    type="Polygon",
                    coordinates=[
                        [
                            [-118.30, 34.00],
                            [-118.20, 34.00],
                            [-118.20, 34.10],
                            [-118.30, 34.10],
                            [-118.30, 34.00],
                        ]
                    ],
                ),
                properties={"name": "Test Square"},
            )
        ],
    )


@pytest.fixture
def multiple_polygons():
    return FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                geometry=Polygon(
                    type="Polygon",
                    coordinates=[
                        [
                            [-118.30, 34.00],
                            [-118.20, 34.00],
                            [-118.20, 34.10],
                            [-118.30, 34.10],
                            [-118.30, 34.00],
                        ]
                    ],
                ),
                properties={"name": "Polygon 1"},
            ),
            Feature(
                type="Feature",
                geometry=Polygon(
                    type="Polygon",
                    coordinates=[
                        [
                            [-118.15, 34.05],
                            [-118.10, 34.05],
                            [-118.10, 34.08],
                            [-118.15, 34.08],
                            [-118.15, 34.05],
                        ]
                    ],
                ),
                properties={"name": "Polygon 2"},
            ),
        ],
    )


def test_manifest(tool):
    manifest = tool.manifest()
    assert manifest.id == "area-perimeter"
    assert manifest.name == "Area & Perimeter Calculator"
    assert manifest.author == "MLee7"
    assert "measurement" in manifest.tags
    assert len(manifest.parameters) == 5


def test_basic_calculation(tool, square_polygon):
    tool_input = ToolInput(geojson=square_polygon, parameters={})
    result = tool.execute(tool_input)

    assert result.result is not None
    assert len(result.result.features) == 1

    feature = result.result.features[0]
    props = feature.properties

    assert "area_sq_m" in props
    assert "perimeter_m" in props
    assert "centroid_lon" in props
    assert "centroid_lat" in props
    assert props["area_sq_m"] > 0
    assert props["perimeter_m"] > 0


def test_metric_units(tool, square_polygon):
    tool_input = ToolInput(
        geojson=square_polygon, parameters={"include_metric": True, "include_imperial": False}
    )
    result = tool.execute(tool_input)

    props = result.result.features[0].properties
    assert "area_sq_km" in props
    assert "perimeter_km" in props
    assert "area_acres" not in props
    assert "area_sq_miles" not in props


def test_imperial_units(tool, square_polygon):
    tool_input = ToolInput(
        geojson=square_polygon, parameters={"include_metric": False, "include_imperial": True}
    )
    result = tool.execute(tool_input)

    props = result.result.features[0].properties
    assert "area_acres" in props
    assert "area_sq_miles" in props
    assert "perimeter_miles" in props
    assert "area_sq_km" not in props
    assert "perimeter_km" not in props


def test_compactness_calculation(tool, square_polygon):
    tool_input = ToolInput(geojson=square_polygon, parameters={"calculate_compactness": True})
    result = tool.execute(tool_input)

    props = result.result.features[0].properties
    assert "compactness_ratio" in props
    assert "shape_description" in props
    assert 0 <= props["compactness_ratio"] <= 1.0


def test_no_compactness(tool, square_polygon):
    tool_input = ToolInput(geojson=square_polygon, parameters={"calculate_compactness": False})
    result = tool.execute(tool_input)

    props = result.result.features[0].properties
    assert "compactness_ratio" not in props
    assert "shape_description" not in props


def test_multiple_features(tool, multiple_polygons):
    tool_input = ToolInput(geojson=multiple_polygons, parameters={})
    result = tool.execute(tool_input)

    assert len(result.result.features) == 2
    for feature in result.result.features:
        assert "area_sq_m" in feature.properties
        assert "perimeter_m" in feature.properties


def test_preserves_original_properties(tool, square_polygon):
    tool_input = ToolInput(geojson=square_polygon, parameters={})
    result = tool.execute(tool_input)

    props = result.result.features[0].properties
    assert props["name"] == "Test Square"


def test_empty_input(tool):
    empty_fc = FeatureCollection(type="FeatureCollection", features=[])
    tool_input = ToolInput(geojson=empty_fc, parameters={})

    with pytest.raises(ValueError, match="No input features provided"):
        tool.execute(tool_input)


def test_warnings(tool, square_polygon):
    tool_input = ToolInput(geojson=square_polygon, parameters={})
    result = tool.execute(tool_input)

    assert result.warnings is not None
    assert len(result.warnings) > 0
    assert any("approximation" in w.lower() for w in result.warnings)
