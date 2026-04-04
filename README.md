# GeoHub — Open Source Geospatial Tool Registry

An open source platform for publishing, discovering, and executing geospatial processing tools through a standardized API.

## Quickstart

```bash
# Install
pip install -e ".[dev]"

# Run
uvicorn hub.main:app --reload

# Test
pytest -v
```

The API is now live at `http://localhost:8000`. Try:

```bash
# List available tools
curl http://localhost:8000/api/v1/tools

# Run a buffer analysis
curl -X POST http://localhost:8000/api/v1/tools/buffer/run \
  -H "Content-Type: application/json" \
  -d '{
    "geojson": {
      "type": "FeatureCollection",
      "features": [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-118.24, 34.05]},
        "properties": {"name": "Downtown LA"}
      }]
    },
    "parameters": {"distance_m": 500}
  }'
```

## API Response Format

Every tool execution returns the same envelope — execution metadata separate from pure GeoJSON:

```jsonc
{
  "execution": {
    "tool_id": "buffer",
    "tool_version": "1.0.0",
    "execution_id": "exec_a1b2c3d4e5f6",
    "execution_time_ms": 12,
    "feature_count": 1,
    "crs": "EPSG:4326",
    "timestamp": "2026-04-03T10:30:00Z",
    "status": "success"
  },
  "result": {
    "type": "FeatureCollection",
    "features": [...]  // pure, spec-compliant GeoJSON
  }
}
```

The `result` field is always a valid GeoJSON FeatureCollection. No custom fields, no extensions. You can paste it directly into geojson.io, load it in QGIS, or feed it to any GeoJSON-compatible tool.

## Building a Tool

### 1. Scaffold

```bash
geohub create-tool my-tool-name --author "Your Name"
```

This creates:
- `tools/my_tool_name/tool.py` — implement your tool here
- `tests/test_my_tool_name.py` — tests

### 2. Implement

Every tool extends `GeoHubTool` and implements two methods:

```python
from sdk.base import GeoHubTool
from sdk.types import ToolManifest, ToolInput, ToolOutput, ParameterSchema

class MyTool(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="my-tool",
            name="My Tool",
            description="What it does",
            parameters=[
                ParameterSchema(
                    name="threshold",
                    type="number",
                    description="Filtering threshold",
                    required=True,
                ),
            ],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        # input.geojson — FeatureCollection with input features
        # input.parameters — dict of parameter values

        # Do your work here...

        return ToolOutput(result=output_feature_collection)
```

### 3. Test

```bash
pytest tests/test_my_tool.py -v
```

### 4. Submit

Open a PR. CI will lint and test. Once merged, the tool is live.

## Project Structure

```
Developer_API_Hub/
├── hub/                    # API server
│   ├── main.py             # FastAPI app + startup
│   ├── config.py           # Settings (env vars)
│   ├── registry.py         # Tool discovery + registration
│   ├── executor.py         # Runs tools, builds response envelope
│   └── routers/
│       └── tools.py        # /api/v1/tools endpoints
├── sdk/                    # Tool SDK (what contributors use)
│   ├── base.py             # GeoHubTool base class
│   ├── types.py            # ToolManifest, ToolInput, ToolOutput, etc.
│   └── cli.py              # `geohub create-tool` scaffolder
├── tools/                  # Published tools (each in its own directory)
│   ├── buffer/tool.py      # Example: buffer analysis
│   └── centroid/tool.py    # Example: centroid computation
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + tool count |
| GET | `/api/v1/tools` | List all tools with manifests |
| GET | `/api/v1/tools/{id}` | Get a single tool's manifest |
| POST | `/api/v1/tools/{id}/run` | Execute a tool |

## Docker

```bash
docker compose up
```

Tools directory is mounted as a volume — add tools without rebuilding.

## License

MIT
