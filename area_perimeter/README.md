# Area & Perimeter Calculator

A GeoHub tool that calculates area and perimeter measurements for polygon features in multiple units.

## Author
MLee7

## Description
This tool takes polygon geometries and calculates comprehensive area and perimeter measurements, including:
- Area in square meters, square kilometers, acres, and square miles
- Perimeter in meters, kilometers, and miles
- Shape compactness ratio (how circular the shape is)
- Centroid coordinates

## Use Cases
- Measure land parcels and property boundaries
- Calculate park and green space sizes
- Estimate building footprints
- Measure water bodies (lakes, ponds)
- Quick area assessments for planning

## Parameters

### Units
- **include_metric** (boolean, default: true) - Include metric units (sq meters, sq km, meters, km)
- **include_imperial** (boolean, default: true) - Include imperial units (acres, sq miles, miles)

### Advanced
- **calculate_compactness** (boolean, default: true) - Calculate shape compactness ratio where 1.0 = perfect circle

## Input
- **Geometry Type**: Polygon or MultiPolygon
- **Draw Modes**: polygon, rectangle
- **Required**: Yes

## Output Properties

### Always Included
- `area_sq_m` - Area in square meters
- `perimeter_m` - Perimeter in meters
- `centroid_lon` - Longitude of centroid
- `centroid_lat` - Latitude of centroid

### Metric Units (if enabled)
- `area_sq_km` - Area in square kilometers
- `perimeter_km` - Perimeter in kilometers

### Imperial Units (if enabled)
- `area_acres` - Area in acres
- `area_sq_miles` - Area in square miles
- `perimeter_miles` - Perimeter in miles

### Compactness (if enabled)
- `compactness_ratio` - Shape compactness (0-1, where 1 is a perfect circle)
- `shape_description` - Text description of shape:
  - "Very compact (near-circular)" - ratio > 0.85
  - "Compact" - ratio > 0.65
  - "Moderately compact" - ratio > 0.40
  - "Elongated or irregular" - ratio ≤ 0.40

## Example Usage

### API Request
```bash
curl -X POST http://localhost:8000/api/v1/tools/area-perimeter/run \
  -H "Content-Type: application/json" \
  -d '{
    "geojson": {
      "type": "FeatureCollection",
      "features": [{
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [[
            [-118.30, 34.00],
            [-118.20, 34.00],
            [-118.20, 34.10],
            [-118.30, 34.10],
            [-118.30, 34.00]
          ]]
        },
        "properties": {"name": "Downtown District"}
      }]
    },
    "parameters": {
      "include_metric": true,
      "include_imperial": true,
      "calculate_compactness": true
    }
  }'
```

### Example Output
```json
{
  "execution": {
    "tool_id": "area-perimeter",
    "status": "success"
  },
  "result": {
    "type": "FeatureCollection",
    "features": [{
      "type": "Feature",
      "geometry": { ... },
      "properties": {
        "name": "Downtown District",
        "area_sq_m": 123456789.12,
        "area_sq_km": 123.46,
        "area_acres": 30512.34,
        "area_sq_miles": 47.67,
        "perimeter_m": 44428.80,
        "perimeter_km": 44.43,
        "perimeter_miles": 27.61,
        "compactness_ratio": 0.7854,
        "shape_description": "Compact",
        "centroid_lon": -118.25,
        "centroid_lat": 34.05
      }
    }]
  }
}
```

## Notes
- Calculations use equatorial approximation (1° ≈ 111.32 km)
- For high-precision measurements near poles, consider using a projected coordinate system
- Original feature properties are preserved in the output
- Compactness ratio of 1.0 represents a perfect circle; lower values indicate more elongated or irregular shapes

## Version
1.0.0
