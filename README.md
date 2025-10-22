# MCP Builder

MCP Builder is an automation tool that ingests API documentation, prompts an LLM for an integration blueprint, and emits a runnable Model Context Protocol (MCP) server that wraps the documented API. The generator is reusable across invocations: every generated server is placed into a shared scaffold that adheres to the open-source MCP specifications.

## Features

- **Automated documentation ingestion** – provide a root URL and the crawler will follow in-domain links, collect textual content, and normalise it for prompting.
- **Reusable MCP scaffold** – all generated projects share infrastructure, configuration, and packaging conventions.
- **LLM-orchestrated codegen** – documentation chunks are supplied to an LLM (OpenAI compatible) that returns structured plans for endpoints and resources. A deterministic fallback heuristic is included for offline scenarios.
- **CLI first** – install the package and invoke `mcp-builder generate <url> <output-dir>` to create a new server project.

## Getting Started

```bash
pip install -e .[llm]
```

Run the generator:

```bash
mcp-builder generate https://example.com/docs ./generated/my_api
```

Alternatively, invoke the automation from Python:

```bash
python scripts/create_mcp_server.py https://example.com/docs ./generated/my_api
```

The command will:

1. Crawl the documentation site and store the extracted corpus.
2. Prompt the configured LLM with the content to obtain a structured integration blueprint.
3. Render the MCP server scaffold, inject the generated endpoints, and write a ready-to-install Python package.

## Development

- `pytest` – run unit tests.
- `mcp-builder generate` – run end-to-end generation.

Set `OPENAI_API_KEY` (or provide your own implementation of `LLMClient`) to enable full LLM-driven planning.
