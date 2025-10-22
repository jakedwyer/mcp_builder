"""Data models used by the ingestion layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class Document:
    """Represents a crawled document."""

    url: str
    content: str
    content_type: str
    metadata: Dict[str, str] = field(default_factory=dict)
    title: Optional[str] = None


@dataclass(slots=True)
class Corpus:
    """Collection of documents."""

    documents: list[Document]

    def concatenate(self, separator: str = "\n\n") -> str:
        """Join all document contents into a single string."""

        return separator.join(doc.content for doc in self.documents)
