"""Centroid — computes centroids of input features."""

from __future__ import annotations

from shapely.geometry import mapping, shape
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Point

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


class CentroidTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="centroid",
            name="Centroid",
            description="Computes the geometric centroid of each input feature.",
            version="1.0.0",
            author="GeoHub",
            tags=["analysis", "geometry", "centroid"],
            parameters=[
                ParameterSchema(
                    name="preserve_properties",
                    type="boolean",
                    description="Copy source feature properties to centroid output",
                    widget="checkbox",
                    required=False,
                    default=True,
                ),
            ],
            geometry_input=GeometryInput(
                required=True,
                accept=[GeometryType.POLYGON, GeometryType.MULTI_POLYGON, GeometryType.LINE_STRING],
                draw_modes=["polygon", "line"],
                description="Features to compute centroids for",
            ),
            output_hints=OutputHints(
                geometry_type=[GeometryType.POINT],
                suggested_display="pins",
                label_property="name",
            ),
            execution=ExecutionConfig(mode="sync", estimated_duration="fast"),
            input_tags=["polygon", "line"],
            output_tags=["point", "analysis"],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        if not input.geojson or not input.geojson.features:
            raise ValueError("No input features provided")

        preserve = input.parameters.get("preserve_properties", True)

        centroid_features = []
        for feature in input.geojson.features:
            geom = shape(feature.geometry.model_dump())
            centroid = geom.centroid

            props = {}
            if preserve and feature.properties:
                props.update(feature.properties)
            props["source_geometry_type"] = feature.geometry.type
            props["centroid_x"] = centroid.x
            props["centroid_y"] = centroid.y

            centroid_features.append(
                Feature(
                    type="Feature",
                    geometry=Point(type="Point", coordinates=[centroid.x, centroid.y]),
                    properties=props,
                )
            )

        return ToolOutput(
            result=FeatureCollection(type="FeatureCollection", features=centroid_features),
        )
