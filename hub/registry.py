"""Tool registry — discovers, registers, and retrieves tools."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from sdk.base import GeoHubTool
from sdk.types import ToolManifest


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, GeoHubTool] = {}

    def register(self, tool: GeoHubTool) -> ToolManifest:
        manifest = tool.manifest()
        self._tools[manifest.id] = tool
        return manifest

    def get(self, tool_id: str) -> GeoHubTool | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[ToolManifest]:
        return [t.manifest() for t in self._tools.values()]

    def discover(self, tools_dir: str = "tools") -> int:
        """Auto-discover tools from the tools/ directory.

        Each subdirectory should contain a tool.py with a class extending GeoHubTool.
        """
        tools_path = Path(tools_dir)
        if not tools_path.exists():
            return 0

        count = 0
        for finder, name, _ in pkgutil.iter_modules([str(tools_path)]):
            try:
                module = importlib.import_module(f"tools.{name}.tool")
                # Find GeoHubTool subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, GeoHubTool)
                        and attr is not GeoHubTool
                    ):
                        self.register(attr())
                        count += 1
            except Exception as e:
                print(f"Warning: Failed to load tool '{name}': {e}")

        return count


# Singleton
registry = ToolRegistry()
