"""Documentation ingestion and crawling utilities."""

from __future__ import annotations

import logging
import queue
import re
from collections.abc import Callable
from dataclasses import dataclass
from html import unescape
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import Corpus, Document

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CrawlConfig:
    """Configuration for the documentation crawler."""

    max_pages: int = 20
    timeout: int = 10
    user_agent: str = "mcp-builder/0.1"
    allow_patterns: tuple[str, ...] = (r".*",)
    deny_patterns: tuple[str, ...] = ()


class DocumentationCrawler:
    """Crawl web documentation and collect textual content."""

    def __init__(
        self,
        start_url: str,
        config: Optional[CrawlConfig] = None,
        session_factory: Callable[[], requests.Session] | None = None,
    ) -> None:
        self.start_url = start_url
        self.config = config or CrawlConfig()
        self.session_factory = session_factory or requests.Session
        self._session: requests.Session | None = None
        self.allowed_netloc = urlparse(start_url).netloc

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = self.session_factory()
            self._session.headers.update({"User-Agent": self.config.user_agent})
        return self._session

    def crawl(self) -> Corpus:
        """Run the crawl returning a :class:`Corpus`."""

        visited: set[str] = set()
        docs: list[Document] = []
        q: queue.Queue[str] = queue.Queue()
        q.put(self.start_url)

        while not q.empty() and len(visited) < self.config.max_pages:
            url = q.get()
            if url in visited:
                continue
            visited.add(url)

            if not self._url_allowed(url):
                logger.debug("Skipping disallowed url %s", url)
                continue

            try:
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Failed to fetch %s: %s", url, exc)
                continue

            content_type = response.headers.get("Content-Type", "text/plain").split(";")[0]
            if content_type.startswith("text/html"):
                document, discovered = self._parse_html(url, response.text)
                docs.append(document)
                for link in discovered:
                    if link not in visited:
                        q.put(link)
            elif content_type == "application/json":
                docs.append(Document(url=url, content=response.text, content_type=content_type))
            else:
                logger.info("Skipping unsupported content type %s from %s", content_type, url)

        return Corpus(documents=docs)

    def _url_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc != self.allowed_netloc:
            return False
        if self.config.allow_patterns and not any(re.fullmatch(pattern, url) for pattern in self.config.allow_patterns):
            return False
        if any(re.fullmatch(pattern, url) for pattern in self.config.deny_patterns):
            return False
        return True

    def _parse_html(self, url: str, html: str) -> tuple[Document, Iterable[str]]:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        for tag in soup(['script', 'style', 'noscript']):
            tag.extract()
        text = soup.get_text(" ", strip=True)
        text = unescape(text)
        links = set()
        for anchor in soup.find_all('a', href=True):
            absolute = urljoin(url, anchor['href'])
            if absolute.startswith("http") and self._url_allowed(absolute):
                links.add(absolute)
        metadata = {"source": url}
        return Document(url=url, content=text, content_type="text/html", metadata=metadata, title=title), links
