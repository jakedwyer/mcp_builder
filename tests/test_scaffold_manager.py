from pathlib import Path

from mcp_builder.orchestration.models import Blueprint, EndpointSpec
from mcp_builder.scaffold.manager import ScaffoldManager


def test_render_project(tmp_path: Path):
    blueprint = Blueprint(
        name="SampleMCP",
        summary="Sample generated project",
        endpoints=[EndpointSpec(name="get_items", method="GET", path="/items", description="List items")],
        prerequisites=["Set API_BASE_URL"],
    )
    manager = ScaffoldManager()
    output = manager.render_project(blueprint, tmp_path / "output")
    assert (output / "README.md").exists()
    assert (output / "pyproject.toml").exists()
    main_py = (output / "server" / "main.py").read_text()
    assert "async def get_items" in main_py
