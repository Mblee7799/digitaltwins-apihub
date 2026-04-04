"""Tool registry and execution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from hub.executor import run_tool
from hub.registry import registry
from sdk.types import ExecutionEnvelope, ToolInput, ToolManifest

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("", response_model=list[ToolManifest])
async def list_tools():
    """List all registered tools."""
    return registry.list_tools()


@router.get("/{tool_id}", response_model=ToolManifest)
async def get_tool(tool_id: str):
    """Get a tool's manifest by ID."""
    tool = registry.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return tool.manifest()


@router.post("/{tool_id}/run", response_model=ExecutionEnvelope)
async def execute_tool(tool_id: str, input: ToolInput):
    """Execute a tool.

    Returns the execution envelope:
    - execution: metadata (tool_id, timing, feature_count, etc.)
    - result: pure GeoJSON FeatureCollection
    """
    tool = registry.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    try:
        return run_tool(tool, input)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")
