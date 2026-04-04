"""Ping — health check tool that returns test features.

Returns "pong" plus a point at Downtown LA and a bounding box
of the contiguous United States. Useful for verifying the full
pipeline works end-to-end.
"""

from __future__ import annotations

from sdk.base import GeoHubTool
from sdk.types import (
    ExecutionConfig,
    GeometryInput,
    GeometryType,
    OutputHints,
    ToolInput,
    ToolManifest,
    ToolOutput,
)

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Point, Polygon


# Contiguous US bounding box (approximate)
CONUS_BBOX = [
    [-124.85, 24.40],  # SW
    [-66.88, 24.40],   # SE
    [-66.88, 49.38],   # NE
    [-124.85, 49.38],  # NW
    [-124.85, 24.40],  # close
]

DTLA = [-118.2437, 34.0522]


class PingTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="ping",
            name="Ping",
            description="Health check — returns 'pong' with test features (DTLA point + CONUS bbox).",
            version="1.0.0",
            author="GeoHub",
            tags=["health", "test", "debug"],
            parameters=[],
            geometry_input=GeometryInput(
                required=False,
                accept=[],
                draw_modes=[],
                description="No input needed",
            ),
            output_hints=OutputHints(
                geometry_type=[GeometryType.POINT, GeometryType.POLYGON],
                suggested_display="auto",
                label_property="name",
            ),
            execution=ExecutionConfig(
                mode="sync",
                estimated_duration="fast",
                idempotent=True,
            ),
            output_tags=["point", "polygon", "test"],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        features = [
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=DTLA),
                properties={
                    "name": "Downtown Los Angeles",
                    "type": "test_point",
                    "message": "pong",
                },
            ),
            Feature(
                type="Feature",
                geometry=Polygon(type="Polygon", coordinates=[CONUS_BBOX]),
                properties={
                    "name": "Contiguous United States",
                    "type": "test_bbox",
                    "message": "pong",
                },
            ),
        ]

        return ToolOutput(
            result=FeatureCollection(type="FeatureCollection", features=features),
        )
