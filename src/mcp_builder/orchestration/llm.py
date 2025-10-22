"""LLM orchestration for generating MCP blueprints."""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Iterable

from .models import Blueprint, EndpointSpec, DEFAULT_BLUEPRINT_NAME

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_blueprint(self, prompt: str) -> Blueprint:
        """Generate a blueprint from the supplied prompt."""


class OpenAILLMClient(LLMClient):
    """OpenAI client implementation."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_blueprint(self, prompt: str) -> Blueprint:
        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": prompt}],
            max_output_tokens=1200,
        )
        content = response.output[0].content[0].text  # type: ignore[attr-defined]
        return self._parse_response(content)

    def _parse_response(self, text: str) -> Blueprint:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model response is not valid JSON: {exc}")
        return blueprint_from_dict(data)


class HeuristicLLMClient(LLMClient):
    """Fallback LLM client that derives endpoints via heuristics."""

    def __init__(self, name: str = DEFAULT_BLUEPRINT_NAME) -> None:
        self.name = name

    def generate_blueprint(self, prompt: str) -> Blueprint:
        endpoints = extract_endpoints(prompt)
        summary = "Heuristically generated MCP server blueprint"
        return Blueprint(name=self.name, summary=summary, endpoints=endpoints)


class LLMOrchestrator:
    """Coordinates prompt creation and blueprint generation."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or HeuristicLLMClient()

    def build_blueprint(self, documents: Iterable[str], title: str | None = None) -> Blueprint:
        prompt = self._build_prompt(documents, title)
        try:
            blueprint = self.llm_client.generate_blueprint(prompt)
        except Exception:
            logger.exception("LLM generation failed, falling back to heuristic parser")
            blueprint = HeuristicLLMClient().generate_blueprint(prompt)
        if not blueprint.endpoints:
            blueprint.endpoints.append(
                EndpointSpec(
                    name="health_check",
                    method="GET",
                    path="/",
                    description="Fallback endpoint returning API availability information.",
                )
            )
        return blueprint

    def _build_prompt(self, documents: Iterable[str], title: str | None) -> str:
        joined = "\n\n".join(documents)
        prompt = (
            "You are an expert software engineer building Model Context Protocol (MCP) servers. "
            "Given the following API documentation, extract the key REST endpoints and return a JSON "
            "object with the fields: name (string), summary (string), endpoints (list of {name, method, path, description}), "
            "and prerequisites (list of strings describing required auth or setup)."
        )
        if title:
            prompt += f"\nDocumentation title: {title}"
        prompt += "\n\nDocumentation:\n" + joined
        return prompt


def extract_endpoints(text: str) -> list[EndpointSpec]:
    """Extract endpoint definitions from raw text using regex heuristics."""

    endpoint_pattern = re.compile(r"(?P<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(?P<path>/[\w\-/{}.:]*)", re.IGNORECASE)
    endpoints: list[EndpointSpec] = []
    for match in endpoint_pattern.finditer(text):
        method = match.group("method").upper()
        path = match.group("path")
        name = slugify(f"{method} {path}")
        description = f"Auto-detected endpoint for {method} {path}"
        endpoints.append(EndpointSpec(name=name, method=method, path=path, description=description))
    return endpoints


def slugify(value: str) -> str:
    """Create a snake_case slug from the input string."""

    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "endpoint"


def blueprint_from_dict(data: dict) -> Blueprint:
    """Convert JSON-like dictionary to :class:`Blueprint`."""

    name = data.get("name") or DEFAULT_BLUEPRINT_NAME
    summary = data.get("summary") or "Generated MCP server"
    endpoint_dicts: Iterable[dict] = data.get("endpoints", [])
    endpoints = [
        EndpointSpec(
            name=item.get("name", slugify(f"{item.get('method', 'get')} {item.get('path', '/')}")),
            method=item.get("method", "GET"),
            path=item.get("path", "/"),
            description=item.get("description", ""),
        )
        for item in endpoint_dicts
    ]
    prerequisites = [str(entry) for entry in data.get("prerequisites", [])]
    return Blueprint(name=name, summary=summary, endpoints=endpoints, prerequisites=prerequisites)
