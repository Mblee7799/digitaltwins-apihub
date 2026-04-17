"""Area & Perimeter Calculator — calculates area and perimeter measurements for polygons."""

from __future__ import annotations

from shapely.geometry import mapping, shape
from geojson_pydantic import Feature, FeatureCollection

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


METERS_TO_KM = 0.001
METERS_TO_MILES = 0.000621371
SQ_METERS_TO_SQ_KM = 0.000001
SQ_METERS_TO_HECTARES = 0.0001
SQ_METERS_TO_ACRES = 0.000247105
SQ_METERS_TO_SQ_MILES = 3.861e-7
PI = 3.14159265359


class AreaPerimeterTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="area-perimeter",
            name="Area & Perimeter Calculator",
            description="Calculate area, perimeter, and shape metrics for land parcels, buildings, or any polygon features. Supports multiple units and provides summary statistics.",
            version="1.1.0",
            author="MLee7",
            tags=["measurement", "geometry", "analysis"],
            parameters=[
                ParameterSchema(
                    name="include_metric",
                    type="boolean",
                    description="Show metric units (hectares, sq km, meters)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Units",
                ),
                ParameterSchema(
                    name="include_imperial",
                    type="boolean",
                    description="Show imperial units (acres, sq miles, feet)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Units",
                ),
                ParameterSchema(
                    name="calculate_compactness",
                    type="boolean",
                    description="Analyze shape compactness (how circular vs elongated)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Analysis",
                ),
                ParameterSchema(
                    name="precision",
                    type="number",
                    description="Decimal places (0=whole numbers, 2=standard, 6=precise)",
                    widget="slider",
                    required=False,
                    default=2,
                    min=0,
                    max=6,
                    step=1,
                    group="Display",
                ),
                ParameterSchema(
                    name="include_summary",
                    type="boolean",
                    description="Show totals and averages when measuring multiple polygons",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Display",
                ),
            ],
            geometry_input=GeometryInput(
                required=True,
                accept=[GeometryType.POLYGON, GeometryType.MULTI_POLYGON],
                draw_modes=["polygon", "rectangle"],
                description="Draw or upload polygon features to measure",
            ),
            output_hints=OutputHints(
                geometry_type=[GeometryType.POLYGON, GeometryType.MULTI_POLYGON],
                suggested_display="choropleth",
                label_property="name",
                color_property="area_sq_m",
            ),
            execution=ExecutionConfig(mode="sync", estimated_duration="fast"),
            input_tags=["polygon"],
            output_tags=["polygon", "measurement", "analysis"],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        if not input.geojson or not input.geojson.features:
            raise ValueError("No input features provided")

        include_metric = input.parameters.get("include_metric", True)
        include_imperial = input.parameters.get("include_imperial", True)
        calculate_compactness = input.parameters.get("calculate_compactness", True)
        include_summary = input.parameters.get("include_summary", True)
        precision = int(input.parameters.get("precision", 2))
        
        total_area = 0
        total_perimeter = 0
        feature_count = 0

        measured_features = []
        for feature in input.geojson.features:
            if feature.geometry is None:
                continue

            try:
                geom = shape(feature.geometry.model_dump())
                
                if not geom.is_valid:
                    geom = geom.buffer(0)
                
                area_sq_m = geom.area * 111320 * 111320
                perimeter_m = geom.length * 111320
            except Exception as e:
                continue

            props = dict(feature.properties or {})

            props["area_sq_m"] = round(area_sq_m, precision)
            props["perimeter_m"] = round(perimeter_m, precision)

            if include_metric:
                props["area_sq_km"] = round(area_sq_m * SQ_METERS_TO_SQ_KM, precision + 2)
                props["area_hectares"] = round(area_sq_m * SQ_METERS_TO_HECTARES, precision + 1)
                props["perimeter_km"] = round(perimeter_m * METERS_TO_KM, precision + 1)

            if include_imperial:
                props["area_acres"] = round(area_sq_m * SQ_METERS_TO_ACRES, precision)
                props["area_sq_miles"] = round(area_sq_m * SQ_METERS_TO_SQ_MILES, precision + 2)
                props["perimeter_miles"] = round(perimeter_m * METERS_TO_MILES, precision + 1)

            if calculate_compactness and area_sq_m > 0 and perimeter_m > 0:
                compactness = (4 * PI * area_sq_m) / (perimeter_m ** 2)
                props["compactness_ratio"] = round(min(compactness, 1.0), max(2, precision))
                
                perimeter_area_ratio = perimeter_m / area_sq_m if area_sq_m > 0 else 0
                props["perimeter_area_ratio"] = round(perimeter_area_ratio, 6)
                
                if compactness > 0.85:
                    props["shape_description"] = "Very compact (near-circular)"
                elif compactness > 0.65:
                    props["shape_description"] = "Compact"
                elif compactness > 0.40:
                    props["shape_description"] = "Moderately compact"
                else:
                    props["shape_description"] = "Elongated or irregular"

            centroid = geom.centroid
            props["centroid_lon"] = round(centroid.x, 6)
            props["centroid_lat"] = round(centroid.y, 6)
            
            units_enabled = []
            if include_metric:
                units_enabled.append("metric")
            if include_imperial:
                units_enabled.append("imperial")
            # Remove internal tracking properties from user view
            # props["units_displayed"] = ", ".join(units_enabled) if units_enabled else "base only"
            # props["precision_level"] = precision
            
            total_area += area_sq_m
            total_perimeter += perimeter_m
            feature_count += 1

            measured_features.append(
                Feature(
                    type="Feature",
                    geometry=feature.geometry,
                    properties=props,
                )
            )

        warnings = []
        if not include_metric and not include_imperial:
            warnings.append("Both metric and imperial units disabled. Only base measurements shown.")
        
        warnings.append("Area and perimeter calculations use equatorial approximation (1° ≈ 111.32 km).")
        
        metrics = None
        if include_summary and feature_count > 1:
            metrics = {
                "summary": {
                    "total_features": feature_count,
                    "total_area_sq_m": round(total_area, precision),
                    "total_perimeter_m": round(total_perimeter, precision),
                    "avg_area_sq_m": round(total_area / feature_count, precision),
                    "avg_perimeter_m": round(total_perimeter / feature_count, precision),
                }
            }
            
            if include_metric:
                metrics["summary"]["total_area_hectares"] = round(total_area * SQ_METERS_TO_HECTARES, precision + 1)
                metrics["summary"]["total_area_sq_km"] = round(total_area * SQ_METERS_TO_SQ_KM, precision + 2)
            
            if include_imperial:
                metrics["summary"]["total_area_acres"] = round(total_area * SQ_METERS_TO_ACRES, precision)
                metrics["summary"]["total_area_sq_miles"] = round(total_area * SQ_METERS_TO_SQ_MILES, precision + 2)

        output = ToolOutput(
            result=FeatureCollection(type="FeatureCollection", features=measured_features),
            warnings=warnings,
        )
        
        if metrics:
            output.metrics = metrics
        
        return output
