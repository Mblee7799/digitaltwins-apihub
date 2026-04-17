# Nearest Feature Finder

A GeoHub tool that finds the closest feature(s) to query points and calculates distances with optional connection line visualization.

## Author
MLee7

## Description
This tool solves the critical "What's closest?" question in spatial analysis. Given query points and target features, it finds the nearest targets, calculates distances, and optionally draws connection lines for visualization.

## Real-World Use Cases
- **Emergency Planning**: "What's the nearest hospital to this accident location?"
- **Retail**: "Which store is closest to this customer address?"
- **Public Services**: "Find the nearest fire station to each neighborhood"
- **Transportation**: "What's the closest bus stop to this building?"
- **Urban Planning**: "Which park is nearest to this residential area?"

## Parameters

### Search
- **k_nearest** (number, default: 1) - Number of nearest features to find (1-10)
- **max_distance_m** (number, default: 0) - Maximum search radius in meters (0 = unlimited)

### Visualization
- **draw_lines** (boolean, default: true) - Draw connection lines from query points to nearest features

### Units
- **include_metric** (boolean, default: true) - Include metric units (meters, km)
- **include_imperial** (boolean, default: true) - Include imperial units (feet, miles)

## Input

### Query Points
- **Geometry Type**: Point or MultiPoint
- **Draw Mode**: point
- **Required**: Yes
- **Properties**: Any properties will be preserved in output

### Target Features
- **How to Mark**: Add `"_is_target": true` to feature properties
- **Example**:
  ```json
  {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-118.25, 34.05]},
    "properties": {
      "name": "Hospital A",
      "_is_target": true,
      "type": "hospital"
    }
  }
  ```

## Output

### Point Features (Results)
Each query point generates k_nearest result points with properties:
- `query_name` - Name of the query point
- `nearest_name` - Name of the closest feature
- `rank` - Ranking (1 = closest, 2 = second closest, etc.)
- `distance_m` - Distance in meters
- `distance_km` - Distance in kilometers (if metric enabled)
- `distance_feet` - Distance in feet (if imperial enabled)
- `distance_miles` - Distance in miles (if imperial enabled)
- `nearest_*` - All properties from the target feature (prefixed with "nearest_")

### Line Features (Connections)
If `draw_lines` is enabled, connection lines show:
- `connection_type` - Always "nearest_path"
- `from` - Query point name
- `to` - Target feature name
- `distance_m` - Distance in meters
- `distance_km` - Distance in kilometers (if metric enabled)
- `distance_miles` - Distance in miles (if imperial enabled)
- `rank` - Ranking of this connection

## Example Usage

### Find Nearest Hospital

```json
{
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.25, 34.05]},
        "properties": {"name": "Accident Location"}
      },
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.26, 34.06]},
        "properties": {
          "name": "City Hospital",
          "_is_target": true,
          "type": "hospital",
          "beds": 250
        }
      },
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.24, 34.04]},
        "properties": {
          "name": "County Medical Center",
          "_is_target": true,
          "type": "hospital",
          "beds": 500
        }
      }
    ]
  },
  "parameters": {
    "k_nearest": 2,
    "draw_lines": true,
    "include_metric": true,
    "include_imperial": true
  }
}
```

### Find Nearest 3 Parks Within 5km

```json
{
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.25, 34.05]},
        "properties": {"name": "My Location"}
      },
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.26, 34.06]},
        "properties": {"name": "Central Park", "_is_target": true}
      },
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.24, 34.04]},
        "properties": {"name": "Echo Park", "_is_target": true}
      },
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.23, 34.03]},
        "properties": {"name": "Griffith Park", "_is_target": true}
      }
    ]
  },
  "parameters": {
    "k_nearest": 3,
    "max_distance_m": 5000,
    "draw_lines": true
  }
}
```

## Example Output

```json
{
  "execution": {
    "tool_id": "nearest-feature",
    "status": "success"
  },
  "result": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.25, 34.05]},
        "properties": {
          "name": "Accident Location",
          "query_name": "Accident Location",
          "nearest_name": "County Medical Center",
          "rank": 1,
          "distance_m": 1567.23,
          "distance_km": 1.567,
          "distance_feet": 5142.48,
          "distance_miles": 0.974,
          "nearest_type": "hospital",
          "nearest_beds": 500
        }
      },
      {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [
            [-118.25, 34.05],
            [-118.24, 34.04]
          ]
        },
        "properties": {
          "connection_type": "nearest_path",
          "from": "Accident Location",
          "to": "County Medical Center",
          "distance_m": 1567.23,
          "distance_km": 1.567,
          "distance_miles": 0.974,
          "rank": 1
        }
      }
    ]
  },
  "warnings": [
    "Distance calculations use equatorial approximation (1° ≈ 111.32 km)."
  ]
}
```

## Tips

1. **Mark Targets**: Always add `"_is_target": true` to features you want to search
2. **Multiple Queries**: You can have multiple query points in one request
3. **Limit Search**: Use `max_distance_m` to exclude features beyond a certain range
4. **Visual Analysis**: Enable `draw_lines` to see connections on the map
5. **Property Transfer**: All target properties are copied to results with "nearest_" prefix

## Notes
- Distance calculations use equatorial approximation (1° ≈ 111.32 km)
- For high-precision measurements near poles, consider using a projected coordinate system
- Connection lines are straight-line distances (as the crow flies), not routing distances
- Original query point properties are preserved in output

## Version
1.0.0
