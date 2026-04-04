"""Tool execution engine — runs tools and wraps results in the execution envelope."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sdk.base import GeoHubTool
from sdk.types import ExecutionEnvelope, ExecutionInfo, ToolInput


def run_tool(tool: GeoHubTool, input: ToolInput) -> ExecutionEnvelope:
    """Execute a tool and return the standard API response envelope."""
    manifest = tool.manifest()

    # Validate input
    errors = tool.validate_input(input)
    if errors:
        raise ValueError(f"Input validation failed: {'; '.join(errors)}")

    # Execute with timing
    start = time.perf_counter()
    output = tool.execute(input)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return ExecutionEnvelope(
        execution=ExecutionInfo(
            tool_id=manifest.id,
            tool_version=manifest.version,
            execution_id=f"exec_{uuid.uuid4().hex[:12]}",
            execution_time_ms=elapsed_ms,
            feature_count=len(output.result.features),
            crs=manifest.output_crs,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status="success",
        ),
        result=output.result,
        warnings=output.warnings,
    )
