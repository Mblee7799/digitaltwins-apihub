"""Nearest Feature Finder — finds the closest feature(s) to a query point or set of points."""

from __future__ import annotations

from shapely.geometry import Point, shape
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import LineString

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


METERS_PER_DEGREE = 111320
METERS_TO_KM = 0.001
METERS_TO_MILES = 0.000621371
METERS_TO_FEET = 3.28084

WALKING_SPEED_MPS = 1.4
BIKING_SPEED_MPS = 4.2
DRIVING_SPEED_MPS = 13.9


def _detect_feature_type(properties: dict) -> str:
    """Detect feature type from properties."""
    if not properties:
        return "feature"
    
    # Check explicit type property
    if "type" in properties:
        return str(properties["type"]).lower()
    if "category" in properties:
        return str(properties["category"]).lower()
    if "facility_type" in properties:
        return str(properties["facility_type"]).lower()
    
    # Check name for common keywords
    name = str(properties.get("name", "")).lower()
    
    # Medical facilities
    if any(word in name for word in ["hospital", "clinic", "medical", "health"]):
        return "hospital"
    
    # Parks and recreation
    if any(word in name for word in ["park", "playground", "recreation", "garden"]):
        return "park"
    
    # Retail
    if any(word in name for word in ["store", "shop", "market", "mall", "walmart", "target"]):
        return "store"
    
    # Emergency services
    if any(word in name for word in ["fire", "police", "station", "emergency"]):
        return "emergency_service"
    
    # Education
    if any(word in name for word in ["school", "university", "college", "library"]):
        return "education"
    
    # Transportation
    if any(word in name for word in ["bus", "metro", "subway", "station", "airport"]):
        return "transit"
    
    # Food
    if any(word in name for word in ["restaurant", "cafe", "coffee", "food"]):
        return "restaurant"
    
    return "feature"


def _calculate_distance(point1: Point, point2: Point) -> float:
    """Calculate approximate distance in meters between two points."""
    dx = (point2.x - point1.x) * METERS_PER_DEGREE
    dy = (point2.y - point1.y) * METERS_PER_DEGREE
    return (dx**2 + dy**2) ** 0.5


class NearestFeatureTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="nearest-feature",
            name="Nearest Feature Finder",
            description="Find the closest hospitals, parks, stores, or any features to your location. Shows distances, travel times, and identifies feature types automatically.",
            version="1.1.0",
            author="MLee7",
            tags=["proximity", "analysis", "distance", "search"],
            parameters=[
                ParameterSchema(
                    name="k_nearest",
                    type="number",
                    description="How many nearest features to find (1=closest only, 3=top 3)",
                    widget="slider",
                    required=False,
                    default=1,
                    min=1,
                    max=10,
                    step=1,
                    group="Search",
                ),
                ParameterSchema(
                    name="max_distance_m",
                    type="number",
                    description="Maximum search radius in meters (0 = no limit)",
                    widget="slider",
                    required=False,
                    default=0,
                    min=0,
                    max=50000,
                    step=500,
                    unit="meters",
                    group="Search",
                ),
                ParameterSchema(
                    name="draw_lines",
                    type="boolean",
                    description="Draw lines showing routes to nearest features",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Display",
                ),
                ParameterSchema(
                    name="include_metric",
                    type="boolean",
                    description="Show metric units (meters, kilometers)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Units",
                ),
                ParameterSchema(
                    name="include_imperial",
                    type="boolean",
                    description="Show imperial units (feet, miles)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Units",
                ),
                ParameterSchema(
                    name="include_travel_time",
                    type="boolean",
                    description="Show estimated travel times (walk, bike, drive)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Analysis",
                ),
                ParameterSchema(
                    name="include_summary",
                    type="boolean",
                    description="Show overall statistics (avg distance, min/max, etc.)",
                    widget="checkbox",
                    required=False,
                    default=True,
                    group="Analysis",
                ),
            ],
            geometry_input=GeometryInput(
                required=True,
                accept=[GeometryType.POINT, GeometryType.MULTI_POINT],
                draw_modes=["point"],
                description="Click on the map to add query points. Mark target features with '_is_target': true property.",
            ),
            output_hints=OutputHints(
                geometry_type=[GeometryType.POINT, GeometryType.LINE_STRING],
                suggested_display="pins",
                label_property="nearest_description",
            ),
            execution=ExecutionConfig(mode="sync", estimated_duration="fast"),
            input_tags=["point"],
            output_tags=["point", "line", "proximity", "analysis"],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        if not input.geojson or not input.geojson.features:
            raise ValueError("No query points provided")

        k_nearest = int(input.parameters.get("k_nearest", 1))
        max_distance_m = float(input.parameters.get("max_distance_m", 0))
        draw_lines = input.parameters.get("draw_lines", True)
        include_metric = input.parameters.get("include_metric", True)
        include_imperial = input.parameters.get("include_imperial", True)
        include_travel_time = input.parameters.get("include_travel_time", True)
        include_summary = input.parameters.get("include_summary", True)
        
        all_distances = []
        queries_processed = 0
        features_within_range = 0

        query_points = []
        target_features = []

        for feature in input.geojson.features:
            if feature.geometry is None:
                continue
            
            geom = shape(feature.geometry.model_dump())
            
            if isinstance(geom, Point):
                props = feature.properties or {}
                if props.get("_is_target", False):
                    target_features.append((geom, feature))
                else:
                    query_points.append((geom, feature))

        if not query_points:
            query_points = [(shape(f.geometry.model_dump()), f) for f in input.geojson.features 
                           if f.geometry is not None]

        if not target_features:
            raise ValueError(
                "No target features found. Add features with property '_is_target': true, "
                "or provide a second feature collection in the input."
            )

        output_features = []
        
        for query_geom, query_feature in query_points:
            queries_processed += 1
            query_props = dict(query_feature.properties or {})
            query_name = query_props.get("name", "Query Point")
            
            distances = []
            for target_geom, target_feature in target_features:
                target_props = target_feature.properties or {}
                distance_m = _calculate_distance(query_geom, target_geom)
                
                if max_distance_m > 0 and distance_m > max_distance_m:
                    continue
                
                distances.append({
                    "distance_m": distance_m,
                    "target_geom": target_geom,
                    "target_feature": target_feature,
                    "target_props": target_props,
                })
            
            if not distances:
                output_features.append(
                    Feature(
                        type="Feature",
                        geometry=query_feature.geometry,
                        properties={
                            **query_props,
                            "status": "no_features_within_range",
                            "search_radius_m": max_distance_m,
                        },
                    )
                )
                continue
            
            distances.sort(key=lambda x: x["distance_m"])
            nearest = distances[:k_nearest]
            
            for i, nearest_item in enumerate(nearest, 1):
                distance_m = nearest_item["distance_m"]
                target_props = nearest_item["target_props"]
                target_geom = nearest_item["target_geom"]
                
                nearest_name = target_props.get("name", f"Feature {i}")
                feature_type = _detect_feature_type(target_props)
                
                result_props = {
                    **query_props,
                    "query_name": query_name,
                    "nearest_name": nearest_name,
                    "nearest_type": feature_type,
                    "nearest_description": f"Nearest {feature_type}: {nearest_name}",
                    "rank": i,
                    "distance_m": round(distance_m, 2),
                }
                
                if include_metric:
                    result_props["distance_km"] = round(distance_m * METERS_TO_KM, 3)
                
                if include_imperial:
                    result_props["distance_feet"] = round(distance_m * METERS_TO_FEET, 2)
                    result_props["distance_miles"] = round(distance_m * METERS_TO_MILES, 3)
                
                if include_travel_time:
                    walk_time_min = (distance_m / WALKING_SPEED_MPS) / 60
                    bike_time_min = (distance_m / BIKING_SPEED_MPS) / 60
                    drive_time_min = (distance_m / DRIVING_SPEED_MPS) / 60
                    
                    result_props["walk_time_min"] = round(walk_time_min, 1)
                    result_props["bike_time_min"] = round(bike_time_min, 1)
                    result_props["drive_time_min"] = round(drive_time_min, 1)
                
                all_distances.append(distance_m)
                features_within_range += 1
                
                for key, value in target_props.items():
                    if key not in result_props and key != "_is_target":
                        result_props[f"nearest_{key}"] = value
                
                output_features.append(
                    Feature(
                        type="Feature",
                        geometry=query_feature.geometry,
                        properties=result_props,
                    )
                )
                
                if draw_lines:
                    line_props = {
                        "connection_type": "nearest_path",
                        "from": query_name,
                        "to": nearest_name,
                        "to_type": feature_type,
                        "description": f"Route to {feature_type}: {nearest_name}",
                        "distance_m": round(distance_m, 2),
                        "rank": i,
                    }
                    
                    if include_metric:
                        line_props["distance_km"] = round(distance_m * METERS_TO_KM, 3)
                    
                    if include_imperial:
                        line_props["distance_miles"] = round(distance_m * METERS_TO_MILES, 3)
                    
                    output_features.append(
                        Feature(
                            type="Feature",
                            geometry=LineString(
                                type="LineString",
                                coordinates=[
                                    [query_geom.x, query_geom.y],
                                    [target_geom.x, target_geom.y],
                                ],
                            ),
                            properties=line_props,
                        )
                    )
        
        warnings = []
        if not target_features:
            warnings.append("No target features provided. Mark features with '_is_target': true property.")
        warnings.append("Distance calculations use equatorial approximation (1° ≈ 111.32 km).")
        if max_distance_m > 0:
            warnings.append(f"Search limited to {max_distance_m}m radius.")
        if include_travel_time:
            warnings.append("Travel times are straight-line estimates. Actual times may vary based on routes and conditions.")
        
        metrics = None
        if include_summary and all_distances:
            avg_distance = sum(all_distances) / len(all_distances)
            min_distance = min(all_distances)
            max_distance = max(all_distances)
            
            metrics = {
                "summary": {
                    "queries_processed": queries_processed,
                    "target_features": len(target_features),
                    "results_found": features_within_range,
                    "avg_distance_m": round(avg_distance, 2),
                    "min_distance_m": round(min_distance, 2),
                    "max_distance_m": round(max_distance, 2),
                }
            }
            
            if include_metric:
                metrics["summary"]["avg_distance_km"] = round(avg_distance * METERS_TO_KM, 3)
            
            if include_imperial:
                metrics["summary"]["avg_distance_miles"] = round(avg_distance * METERS_TO_MILES, 3)
            
            if include_travel_time:
                avg_walk = (avg_distance / WALKING_SPEED_MPS) / 60
                metrics["summary"]["avg_walk_time_min"] = round(avg_walk, 1)
        
        output = ToolOutput(
            result=FeatureCollection(type="FeatureCollection", features=output_features),
            warnings=warnings,
        )
        
        if metrics:
            output.metrics = metrics
        
        return output
