"""Helper script to invoke the MCP builder programmatically."""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp_builder.project.generator import ProjectGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an MCP server from API docs")
    parser.add_argument("url", help="Root URL of the API documentation")
    parser.add_argument("output", type=Path, help="Destination directory for the generated project")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum number of pages to crawl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = ProjectGenerator()
    generator.generate(args.url, args.output, max_pages=args.max_pages)


if __name__ == "__main__":
    main()
