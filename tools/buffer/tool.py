"""Buffer Analysis — creates buffer polygons around input features."""

from __future__ import annotations

from shapely import buffer
from shapely.geometry import mapping, shape
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon

from sdk.base import GeoHubTool
from sdk.types import (
    ExecutionConfig,
    GeometryInput,
    GeometryType,
    OutputHints,
    ParameterSchema,
    ToolInput,
    ToolManifest,
    ToolOutput,
)


class BufferTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="buffer",
            name="Buffer Analysis",
            description="Creates buffer polygons around input features at a specified distance.",
            version="1.0.0",
            author="GeoHub",
            tags=["analysis", "proximity", "buffer"],
            parameters=[
                ParameterSchema(
                    name="distance_m",
                    type="number",
                    description="Buffer distance",
                    widget="slider",
                    min=0,
                    max=50000,
                    step=100,
                    unit="meters",
                    group="analysis",
                ),
                ParameterSchema(
                    name="resolution",
                    type="number",
                    description="Smoothness (segments per quarter circle)",
                    widget="slider",
                    required=False,
                    default=16,
                    min=4,
                    max=64,
                    step=4,
                    group="advanced",
                ),
            ],
            geometry_input=GeometryInput(
                required=True,
                accept=[GeometryType.POINT, GeometryType.LINE_STRING, GeometryType.POLYGON],
                draw_modes=["point", "line", "polygon"],
                description="Features to buffer",
            ),
            output_hints=OutputHints(
                geometry_type=[GeometryType.POLYGON],
                suggested_display="choropleth",
                label_property="name",
            ),
            execution=ExecutionConfig(mode="sync", estimated_duration="fast"),
            input_tags=["point", "line", "polygon"],
            output_tags=["polygon", "analysis"],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        if not input.geojson or not input.geojson.features:
            raise ValueError("No input features provided")

        distance_m = input.parameters["distance_m"]
        resolution = input.parameters.get("resolution", 16)
        distance_deg = distance_m / 111_320

        buffered_features = []
        for feature in input.geojson.features:
            geom = shape(feature.geometry.model_dump())
            buffered_geom = buffer(geom, distance_deg, quad_segs=resolution)

            buffered_features.append(
                Feature(
                    type="Feature",
                    geometry=Polygon(**mapping(buffered_geom)),
                    properties={
                        **(feature.properties or {}),
                        "buffer_distance_m": distance_m,
                        "area_sq_deg": buffered_geom.area,
                    },
                )
            )

        return ToolOutput(
            result=FeatureCollection(type="FeatureCollection", features=buffered_features),
            warnings=["Distance conversion uses equatorial approximation (1 deg ~ 111.32 km)"],
        )
