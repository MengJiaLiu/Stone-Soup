"""Dataclass representing a single academic paper.

Used throughout the ``paper_assistant`` package to hold normalised paper
metadata regardless of the source (arXiv, DBLP, etc.).
"""

from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass
class Paper:
    """Normalised representation of an academic paper.

    Attributes
    ----------
    title:
        Full paper title.
    authors:
        List of author names (first-last format).
    abstract:
        Paper abstract or summary.
    url:
        Canonical URL (PDF or landing page).
    pdf_url:
        Direct link to the PDF, if available.
    arxiv_id:
        arXiv identifier (e.g. ``"2401.12345"``), if applicable.
    doi:
        Digital Object Identifier, if available.
    year:
        Publication year.
    venue:
        Conference or journal name.
    keywords:
        List of author-supplied or inferred keywords.
    """

    title: str
    authors: list[str]
    abstract: str = ""
    url: str = ""
    pdf_url: str = ""
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    venue: str = ""
    keywords: list[str] = dataclasses.field(default_factory=list)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def short_title(self) -> str:
        """Return title truncated to 60 characters."""
        return self.title if len(self.title) <= 60 else self.title[:57] + "..."

    def __str__(self) -> str:  # pragma: no cover
        authors = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors += " et al."
        return f"{self.title} — {authors} ({self.year})"
