"""CLI entry point for the MCP builder."""

from __future__ import annotations

import logging
from pathlib import Path

import typer

from .project.generator import ProjectGenerator

logging.basicConfig(level=logging.INFO)

app = typer.Typer(help="Automate MCP server generation from API documentation")


@app.command()
def generate(
    url: str = typer.Argument(..., help="Root URL of the API documentation"),
    output_dir: Path = typer.Argument(..., help="Directory to write the generated MCP project"),
    max_pages: int = typer.Option(20, help="Maximum number of documentation pages to crawl"),
) -> None:
    """Generate an MCP server from the provided documentation URL."""

    generator = ProjectGenerator()
    generator.generate(url, output_dir, max_pages=max_pages)
    typer.echo(f"Project written to {output_dir}")


if __name__ == "__main__":
    app()
