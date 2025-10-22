"""Handles rendering the reusable MCP scaffold."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ..orchestration.models import Blueprint

logger = logging.getLogger(__name__)


def _default_env(template_dir: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env


class ScaffoldManager:
    """Render templates to produce a runnable MCP server."""

    def __init__(self, template_dir: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.template_dir = template_dir or root / "templates" / "mcp_server"
        self.env = _default_env(self.template_dir)

    def render_project(self, blueprint: Blueprint, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        context = self._context_from_blueprint(blueprint)
        for template_path in self.template_dir.rglob("*.j2"):
            relative = template_path.relative_to(self.template_dir)
            destination = output_dir / relative.with_suffix("")
            destination.parent.mkdir(parents=True, exist_ok=True)
            template = self.env.get_template(str(relative))
            content = template.render(**context)
            destination.write_text(content, encoding="utf-8")
            logger.debug("Rendered %s", destination)
        (output_dir / "blueprint.json").write_text(json.dumps(context["blueprint"], indent=2), encoding="utf-8")
        return output_dir

    def _context_from_blueprint(self, blueprint: Blueprint) -> dict[str, Any]:
        return {
            "blueprint": {
                "name": blueprint.name,
                "summary": blueprint.summary,
                "endpoints": [
                    {
                        "name": ep.name,
                        "method": ep.method,
                        "path": ep.path,
                        "description": ep.description,
                    }
                    for ep in blueprint.endpoints
                ],
                "prerequisites": blueprint.prerequisites,
            }
        }
