"""Data structures describing generated MCP projects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class EndpointSpec:
    """Represents an API endpoint to be wrapped."""

    name: str
    method: str
    path: str
    description: str


@dataclass(slots=True)
class Blueprint:
    """Full blueprint for an MCP server implementation."""

    name: str
    summary: str
    endpoints: List[EndpointSpec] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)


DEFAULT_BLUEPRINT_NAME = "GeneratedMCPServer"
