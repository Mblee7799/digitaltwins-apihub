"""Core types for the GeoHub Tool SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any

from geojson_pydantic import FeatureCollection
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GeometryType(str, Enum):
    POINT = "Point"
    MULTI_POINT = "MultiPoint"
    LINE_STRING = "LineString"
    MULTI_LINE_STRING = "MultiLineString"
    POLYGON = "Polygon"
    MULTI_POLYGON = "MultiPolygon"
    GEOMETRY_COLLECTION = "GeometryCollection"
    ANY = "Any"


# ---------------------------------------------------------------------------
# Parameter UI schema — drives form generation in any consuming app
# ---------------------------------------------------------------------------

class ParameterSchema(BaseModel):
    """Describes a single tool parameter and how to render it."""

    name: str
    type: str  # "number", "string", "boolean"
    description: str
    required: bool = True
    default: Any = None

    # UI hints
    widget: str = "auto"  # "slider", "textbox", "checkbox", "dropdown", "color", "auto"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    enum: list[str] | None = None
    placeholder: str | None = None
    unit: str | None = None  # "meters", "degrees", "km"
    group: str | None = None  # group related params in UI sections


# ---------------------------------------------------------------------------
# Geometry input config — tells the UI which draw tools to activate
# ---------------------------------------------------------------------------

class GeometryInput(BaseModel):
    """Declares what geometry a tool needs from the user."""

    required: bool = True
    accept: list[GeometryType] = [GeometryType.ANY]
    draw_modes: list[str] = []  # "point", "polygon", "rectangle", "line"
    max_features: int | None = None
    description: str = ""


# ---------------------------------------------------------------------------
# Output hints — tells consumers how to render results
# ---------------------------------------------------------------------------

class OutputHints(BaseModel):
    """Suggests how results should be visualized."""

    geometry_type: list[GeometryType] = [GeometryType.ANY]
    suggested_display: str = "auto"  # "pins", "choropleth", "heatmap", "lines", "clusters"
    label_property: str | None = None
    color_property: str | None = None
    sort_property: str | None = None


# ---------------------------------------------------------------------------
# Execution config — sync vs async, estimated cost
# ---------------------------------------------------------------------------

class ExecutionConfig(BaseModel):
    """Declares how a tool runs."""

    mode: str = "sync"  # "sync", "async", "streaming"
    estimated_duration: str = "fast"  # "fast" (<5s), "medium" (<30s), "slow" (>30s)
    idempotent: bool = True


# ---------------------------------------------------------------------------
# External requirements — API keys, services a tool depends on
# ---------------------------------------------------------------------------

class ExternalRequirements(BaseModel):
    """Declares external dependencies."""

    apis: list[str] = []  # ["openmeteo", "census.gov"]
    secrets: list[str] = []  # ["CENSUS_API_KEY"] — consumer must provide


# ---------------------------------------------------------------------------
# Tool manifest — the full self-description
# ---------------------------------------------------------------------------

class ToolManifest(BaseModel):
    """Everything a consuming app needs to build UI, execute, and display results."""

    id: str = Field(description="Unique tool identifier, e.g. 'buffer-analysis'")
    name: str = Field(description="Human-readable name")
    description: str
    version: str = "0.1.0"
    author: str = ""
    license: str = "MIT"
    tags: list[str] = []

    # Input
    parameters: list[ParameterSchema] = []
    geometry_input: GeometryInput = Field(default_factory=GeometryInput)

    # Output
    output_hints: OutputHints = Field(default_factory=OutputHints)
    output_crs: str = "EPSG:4326"

    # Execution
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)

    # Chaining — enables pipeline builders
    input_tags: list[str] = []  # accepts output tagged as these
    output_tags: list[str] = []  # tags this tool's output

    # External deps
    requirements: ExternalRequirements = Field(default_factory=ExternalRequirements)


# ---------------------------------------------------------------------------
# Tool I/O — what flows through execute()
# ---------------------------------------------------------------------------

class ToolInput(BaseModel):
    """Standard input envelope for tool execution."""

    geojson: FeatureCollection | None = None
    parameters: dict[str, Any] = {}


class ToolOutput(BaseModel):
    """Standard output — pure GeoJSON result with optional warnings."""

    result: FeatureCollection
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# API response envelope — wraps tool output with execution telemetry
# ---------------------------------------------------------------------------

class ExecutionInfo(BaseModel):
    """System-produced execution telemetry."""

    tool_id: str
    tool_version: str
    execution_id: str
    execution_time_ms: int
    feature_count: int
    crs: str = "EPSG:4326"
    timestamp: str
    status: str = "success"


class ExecutionEnvelope(BaseModel):
    """API response: execution telemetry + pure GeoJSON result."""

    execution: ExecutionInfo
    result: FeatureCollection
    warnings: list[str] = []
