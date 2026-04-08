"""Environmental Check — returns metrics for a coordinate.

Example tool demonstrating metrics-only output (no geometry returned),
coordinate input, and external API secret requirements.
This is the pattern interns will use for tools like air quality,
temperature, wildfire risk, etc.
"""

from __future__ import annotations

import random

from sdk.base import GeoHubTool
from sdk.types import (
    ExecutionConfig,
    ExternalRequirements,
    GeometryInput,
    GeometryType,
    OutputHints,
    ParameterSchema,
    ToolInput,
    ToolManifest,
    ToolOutput,
)


class EnvCheckTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="env-check",
            name="Environmental Check",
            description="Returns simulated environmental metrics for a location. "
                        "Demonstrates the pattern for API-backed, metrics-only tools.",
            version="0.1.0",
            author="GeoHub",
            tags=["environment", "metrics", "air-quality", "demo"],
            parameters=[
                ParameterSchema(
                    name="latitude",
                    type="number",
                    description="Latitude",
                    widget="coordinates",
                    min=-90,
                    max=90,
                    placeholder="34.0522",
                    group="location",
                ),
                ParameterSchema(
                    name="longitude",
                    type="number",
                    description="Longitude",
                    widget="coordinates",
                    min=-180,
                    max=180,
                    placeholder="-118.2437",
                    group="location",
                ),
            ],
            geometry_input=GeometryInput(
                required=False,
                accept=[GeometryType.POINT],
                draw_modes=["click"],
                description="Click a location on the map, or enter coordinates",
            ),
            output_hints=OutputHints(
                geometry_type=[],
                suggested_display="dashboard",
            ),
            execution=ExecutionConfig(
                mode="sync",
                estimated_duration="medium",
            ),
            requirements=ExternalRequirements(
                apis=["google_air_quality", "nasa_power"],
                secrets=["GOOGLE_MAPS_KEY"],
            ),
            output_tags=["metrics", "environment"],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        lat = input.parameters.get("latitude")
        lng = input.parameters.get("longitude")

        # Also accept geometry click as input
        if (lat is None or lng is None) and input.geojson and input.geojson.features:
            geom = input.geojson.features[0].geometry
            if hasattr(geom, "coordinates"):
                coords = geom.coordinates  # type: ignore[union-attr]
                lng, lat = coords[0], coords[1]

        if lat is None or lng is None:
            raise ValueError("Provide latitude/longitude or click a point on the map")

        # Simulated environmental data
        # In a real tool, this calls Google Air Quality API, NASA POWER, etc.
        # using input.secrets["GOOGLE_MAPS_KEY"]
        metrics = {
            "location": {"latitude": lat, "longitude": lng},
            "air_quality": {
                "aqi": random.randint(30, 150),
                "pm25": round(random.uniform(5, 40), 1),
                "pm10": round(random.uniform(10, 80), 1),
                "dominant_pollutant": random.choice(["PM2.5", "O3", "NO2"]),
                "category": random.choice(["Good", "Moderate", "Unhealthy for Sensitive Groups"]),
            },
            "temperature": {
                "surface_temp_f": round(random.uniform(65, 105), 1),
                "heat_index": random.choice(["Low", "Moderate", "High", "Very High"]),
            },
            "vegetation": {
                "ndvi": round(random.uniform(0.05, 0.65), 3),
                "tree_canopy_pct": round(random.uniform(2, 45), 1),
            },
        }

        tables = [
            {"metric": "Air Quality Index", "value": metrics["air_quality"]["aqi"], "unit": "AQI", "status": metrics["air_quality"]["category"]},
            {"metric": "PM2.5", "value": metrics["air_quality"]["pm25"], "unit": "μg/m³", "status": "—"},
            {"metric": "Surface Temperature", "value": metrics["temperature"]["surface_temp_f"], "unit": "°F", "status": metrics["temperature"]["heat_index"]},
            {"metric": "Tree Canopy", "value": metrics["vegetation"]["tree_canopy_pct"], "unit": "%", "status": "—"},
            {"metric": "NDVI", "value": metrics["vegetation"]["ndvi"], "unit": "index", "status": "—"},
        ]

        return ToolOutput(
            result=None,
            metrics=metrics,
            tables=tables,
            warnings=["Values are simulated. Connect API keys for real data."],
        )
