"""Coordinates the end-to-end MCP project generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from ..ingestion.downloader import CrawlConfig, DocumentationCrawler
from ..ingestion.models import Corpus
from ..orchestration.llm import LLMOrchestrator
from ..scaffold.manager import ScaffoldManager

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """High level façade that coordinates the generator pipeline."""

    def __init__(
        self,
        orchestrator: LLMOrchestrator | None = None,
        scaffold_manager: ScaffoldManager | None = None,
    ) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()
        self.scaffold_manager = scaffold_manager or ScaffoldManager()

    def generate(self, url: str, output_dir: Path, max_pages: int = 20) -> Path:
        """Generate the MCP project for the supplied URL."""

        logger.info("Starting project generation for %s", url)
        crawler = DocumentationCrawler(url, config=CrawlConfig(max_pages=max_pages))
        corpus = crawler.crawl()
        logger.info("Collected %d documents", len(corpus.documents))
        blueprint = self.orchestrator.build_blueprint(self._document_texts(corpus), title=corpus.documents[0].title if corpus.documents else None)
        logger.info("Generated blueprint with %d endpoints", len(blueprint.endpoints))
        project_path = self.scaffold_manager.render_project(blueprint, output_dir)
        logger.info("Project written to %s", project_path)
        return project_path

    def _document_texts(self, corpus: Corpus) -> Iterable[str]:
        for doc in corpus.documents:
            yield f"Source: {doc.url}\n\n{doc.content}"
