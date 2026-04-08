"""Base class all GeoHub tools extend."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sdk.types import ToolInput, ToolManifest, ToolOutput


class GeoHubTool(ABC):
    """
    Base class for all GeoHub tools.

    Interns subclass this, implement manifest() and execute(), done.

    Example:
        class BufferTool(GeoHubTool):
            def manifest(self) -> ToolManifest:
                return ToolManifest(
                    id="buffer",
                    name="Buffer Analysis",
                    description="Creates buffer polygons around features",
                    parameters=[...],
                )

            def execute(self, input: ToolInput) -> ToolOutput:
                # do the work
                return ToolOutput(result=buffered_fc)
    """

    @abstractmethod
    def manifest(self) -> ToolManifest:
        """Return the tool's manifest describing its capabilities."""
        ...

    @abstractmethod
    def execute(self, input: ToolInput) -> ToolOutput:
        """Execute the tool and return pure GeoJSON results."""
        ...

    def validate_input(self, input: ToolInput) -> list[str]:
        """Optional input validation. Return list of error messages."""
        errors = []
        manifest = self.manifest()
        has_geojson = input.geojson is not None and bool(input.geojson.features)

        for param in manifest.parameters:
            if param.required and param.name not in input.parameters:
                # Coordinate params can be satisfied by geojson input instead
                if param.widget == "coordinates" and has_geojson:
                    continue
                errors.append(f"Missing required parameter: {param.name}")

        return errors
