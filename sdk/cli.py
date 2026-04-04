"""CLI for GeoHub tool development.

Usage:
    python -m sdk.cli create-tool my-tool-name
    python -m sdk.cli list-tools
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOL_TEMPLATE = '''"""{{name}} — describe what this tool does.

Created by: {{author}}
"""

from __future__ import annotations

from shapely.geometry import mapping, shape
from geojson_pydantic import Feature, FeatureCollection

from sdk.base import GeoHubTool
from sdk.types import (
    GeometryType,
    ParameterSchema,
    ToolInput,
    ToolManifest,
    ToolOutput,
)


class {{class_name}}(GeoHubTool):
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            id="{{id}}",
            name="{{name}}",
            description="TODO: Describe what this tool does",
            version="0.1.0",
            author="{{author}}",
            tags=[],
            parameters=[
                # Add your parameters here:
                # ParameterSchema(
                #     name="param_name",
                #     type="number",
                #     description="What this parameter does",
                #     required=True,
                # ),
            ],
            accepts_geometry=[GeometryType.ANY],
            outputs_geometry=[GeometryType.ANY],
        )

    def execute(self, input: ToolInput) -> ToolOutput:
        if not input.geojson or not input.geojson.features:
            raise ValueError("No input features provided")

        output_features = []
        for feature in input.geojson.features:
            geom = shape(feature.geometry.model_dump())

            # TODO: Transform the geometry / compute results
            result_geom = geom

            output_features.append(
                Feature(
                    type="Feature",
                    geometry=result_geom.__geo_interface__,
                    properties={
                        **(feature.properties or {}),
                        # TODO: Add output properties
                    },
                )
            )

        return ToolOutput(
            result=FeatureCollection(
                type="FeatureCollection", features=output_features
            ),
        )
'''

TEST_TEMPLATE = '''"""Tests for {{id}} tool."""

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Point

from sdk.types import ToolInput
from tools.{{id_underscore}}.tool import {{class_name}}


def test_manifest():
    tool = {{class_name}}()
    m = tool.manifest()
    assert m.id == "{{id}}"
    assert m.name


def test_execute():
    tool = {{class_name}}()
    fc = FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                geometry=Point(type="Point", coordinates=[-118.24, 34.05]),
                properties={"name": "test"},
            )
        ],
    )
    result = tool.execute(ToolInput(geojson=fc, parameters={}))
    assert result.result.features
'''


def to_class_name(tool_id: str) -> str:
    return "".join(word.capitalize() for word in tool_id.replace("-", "_").split("_")) + "Tool"


def create_tool(name: str, author: str = "") -> None:
    tool_id = name.lower().replace(" ", "-")
    id_underscore = tool_id.replace("-", "_")
    class_name = to_class_name(tool_id)

    tool_dir = Path("tools") / id_underscore
    if tool_dir.exists():
        print(f"Error: Tool directory '{tool_dir}' already exists")
        sys.exit(1)

    tool_dir.mkdir(parents=True)

    # __init__.py
    (tool_dir / "__init__.py").write_text("")

    # tool.py
    tool_code = (
        TOOL_TEMPLATE.replace("{{name}}", name)
        .replace("{{id}}", tool_id)
        .replace("{{class_name}}", class_name)
        .replace("{{author}}", author)
    )
    (tool_dir / "tool.py").write_text(tool_code)

    # test
    test_code = (
        TEST_TEMPLATE.replace("{{id}}", tool_id)
        .replace("{{id_underscore}}", id_underscore)
        .replace("{{class_name}}", class_name)
    )
    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / f"test_{id_underscore}.py").write_text(test_code)

    print(f"Created tool '{tool_id}':")
    print(f"  {tool_dir}/tool.py       ← implement your tool here")
    print(f"  tests/test_{id_underscore}.py  ← tests")
    print()
    print("Next steps:")
    print(f"  1. Edit {tool_dir}/tool.py — fill in manifest and execute()")
    print(f"  2. Run: pytest tests/test_{id_underscore}.py")
    print(f"  3. Test live: uvicorn hub.main:app --reload")
    print(f"  4. Open PR!")


def main():
    parser = argparse.ArgumentParser(description="GeoHub Tool CLI")
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create-tool", help="Scaffold a new tool")
    create.add_argument("name", help="Tool name (e.g. 'buffer-analysis')")
    create.add_argument("--author", default="", help="Author name")

    sub.add_parser("list-tools", help="List discovered tools")

    args = parser.parse_args()

    if args.command == "create-tool":
        create_tool(args.name, args.author)
    elif args.command == "list-tools":
        from hub.registry import registry
        registry.discover()
        for m in registry.list_tools():
            print(f"  {m.id} v{m.version} — {m.description}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
