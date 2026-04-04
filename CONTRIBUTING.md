# Contributing to GeoHub

Welcome! This guide walks you through creating and publishing a geospatial tool.

## Prerequisites

- Python 3.11+
- Git
- A GitHub account

## Setup (One-Time)

### 1. Fork the Repository

Click **Fork** on the GitHub repo page to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/geohub.git
cd geohub
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Verify Everything Works

```bash
python -m pytest -v
```

You should see all tests pass. You're ready to build a tool.

## Building a Tool

### Step 1: Scaffold

```bash
python -m sdk.cli create-tool my-tool-name --author "Your Name"
```

This creates:
```
tools/my_tool_name/
├── __init__.py
└── tool.py        ← your code goes here

tests/
└── test_my_tool_name.py  ← your tests
```

### Step 2: Implement

Open `tools/my_tool_name/tool.py`. You'll see a template with two methods to fill in:

**`manifest()`** — Declares what your tool does, what inputs it needs, and how to display results:

```python
def manifest(self) -> ToolManifest:
    return ToolManifest(
        id="my-tool-name",
        name="My Tool",
        description="What it does in one sentence",
        version="0.1.0",
        author="Your Name",
        tags=["analysis", "geometry"],

        # Parameters — these become form widgets in the UI
        parameters=[
            ParameterSchema(
                name="distance_m",
                type="number",
                description="Buffer distance",
                widget="slider",        # slider, textbox, checkbox, dropdown
                min=0, max=50000,
                step=100,
                unit="meters",
                group="analysis",
            ),
        ],

        # What geometry does your tool need?
        geometry_input=GeometryInput(
            required=True,
            accept=[GeometryType.POINT, GeometryType.POLYGON],
            draw_modes=["point", "polygon"],
            description="Features to process",
        ),

        # How should results be displayed?
        output_hints=OutputHints(
            geometry_type=[GeometryType.POLYGON],
            suggested_display="choropleth",  # pins, choropleth, heatmap, lines
            label_property="name",
        ),
    )
```

**`execute()`** — Does the actual work:

```python
def execute(self, input: ToolInput) -> ToolOutput:
    # input.geojson — FeatureCollection (or None if geometry not required)
    # input.parameters — dict of parameter values from the form

    features = []
    for feature in input.geojson.features:
        geom = shape(feature.geometry.model_dump())

        # Your processing here...
        result_geom = geom.buffer(0.01)

        features.append(Feature(
            type="Feature",
            geometry=Polygon(**mapping(result_geom)),
            properties={
                **(feature.properties or {}),
                "your_output": "value",
            },
        ))

    return ToolOutput(
        result=FeatureCollection(type="FeatureCollection", features=features),
        warnings=["Optional warnings for the user"],
    )
```

### Step 3: Test

```bash
# Run your test
python -m pytest tests/test_my_tool_name.py -v

# Run ALL tests (make sure you didn't break anything)
python -m pytest -v
```

### Step 4: Test Live

Start the API server and the playground:

```bash
# Terminal 1 — backend
uvicorn hub.main:app --reload

# Terminal 2 — playground
cd playground
npm install  # first time only
npm run dev
```

Open `http://localhost:5173`. Your tool should appear in the sidebar. Select it, fill in the form, and click Run.

### Step 5: Submit a PR

```bash
# Create a branch
git checkout -b add-my-tool-name

# Stage your files
git add tools/my_tool_name/ tests/test_my_tool_name.py

# Commit
git commit -m "Add my-tool-name: brief description of what it does"

# Push to your fork
git push origin add-my-tool-name
```

Then open a Pull Request on GitHub from your branch to `main`.

## What Makes a Good Tool

- **Clear manifest** — Description should tell users what the tool does without jargon
- **Sensible parameter defaults** — Tools should work with defaults where possible
- **Good widget choices** — Use sliders for numeric ranges, dropdowns for enums
- **Handles edge cases** — Empty inputs, single features, etc.
- **Tests pass** — Both your tests and existing tests

## What Goes Where

| Your output | Where it belongs |
|---|---|
| Computed values | `properties` on each Feature |
| Transformed geometries | `geometry` on each Feature |
| User warnings | `warnings` list in ToolOutput |
| UI rendering hints | `output_hints` in manifest |
| Form controls | `parameters` with `widget` in manifest |

**Do NOT** put rendering instructions, style info, or UI behavior in feature properties. That's the consuming application's job. Your tool outputs data; the app decides how to display it.

## Available Widgets

| Widget | Use for | Parameters |
|---|---|---|
| `slider` | Numeric ranges | `min`, `max`, `step`, `unit` |
| `textbox` | Free text or numbers | `placeholder` |
| `checkbox` | Boolean toggles | `default` |
| `dropdown` | Fixed choices | `enum` |
| `color` | Color selection | — |
| `auto` | Let the UI decide | (default) |

## Common Libraries

These are already installed and available:

- **shapely** — Geometry operations (buffer, intersection, union, etc.)
- **geojson-pydantic** — GeoJSON type validation
- **pydantic** — Data validation

If your tool needs additional packages, add them to the `dependencies` list in `pyproject.toml` in your PR.

## Getting Help

- Look at `tools/buffer/tool.py` and `tools/centroid/tool.py` for working examples
- Check the ping tool (`tools/ping/tool.py`) for a minimal no-input example
- Run `python -m sdk.cli list-tools` to see all registered tools
- Open an issue on GitHub if you're stuck

## Code Style

- We use **ruff** for linting: `ruff check .`
- CI runs lint + tests on every PR
- Keep your tool focused — one tool, one job
