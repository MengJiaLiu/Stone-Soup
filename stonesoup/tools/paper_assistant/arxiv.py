"""Fetch the latest papers from the arXiv API.

Uses the public `arXiv API <https://arxiv.org/help/api/index>`_ — no API key
required.

Example
-------
>>> from stonesoup.tools.paper_assistant.arxiv import ArxivFetcher
>>> fetcher = ArxivFetcher(categories=["cs.CV"], max_results=5)
>>> papers = fetcher.fetch()
>>> len(papers) <= 5
True
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Optional

from .models import Paper

_ARXIV_API = "https://export.arxiv.org/api/query"
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivFetcher:
    """Fetch recent papers from arXiv.

    Parameters
    ----------
    categories:
        One or more arXiv category codes (e.g. ``["cs.CV", "eess.SP"]``).
        If *keywords* is also supplied the query uses both.
    keywords:
        Free-text search terms added to the query.
    max_results:
        Maximum number of results to return per call (default ``20``).
    days_back:
        When ``since_date`` is not provided, fetch papers submitted within
        this many days (default ``1`` — today's papers only).
    since_date:
        Explicit start date for the date filter.  ``days_back`` is ignored
        when this is set.
    """

    def __init__(
        self,
        categories: Optional[list[str]] = None,
        keywords: Optional[list[str]] = None,
        max_results: int = 20,
        days_back: int = 1,
        since_date: Optional[date] = None,
    ) -> None:
        if not categories and not keywords:
            raise ValueError("Supply at least one of 'categories' or 'keywords'.")
        self.categories = categories or []
        self.keywords = keywords or []
        self.max_results = max_results
        self.days_back = days_back
        self.since_date = since_date

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> list[Paper]:
        """Fetch papers and return a list of :class:`~.Paper` objects."""
        query = self._build_query()
        params = urllib.parse.urlencode({
            "search_query": query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        url = f"{_ARXIV_API}?{params}"
        with urllib.request.urlopen(url) as resp:  # noqa: S310
            raw = resp.read()
        return self._parse(raw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_query(self) -> str:
        parts: list[str] = []
        for cat in self.categories:
            parts.append(f"cat:{cat}")
        for kw in self.keywords:
            parts.append(f"all:{urllib.parse.quote(kw)}")
        base = " OR ".join(parts)

        # Date filter
        cutoff = self.since_date or (date.today() - timedelta(days=self.days_back))
        date_str = cutoff.strftime("%Y%m%d")
        today_str = date.today().strftime("%Y%m%d")
        date_filter = f"submittedDate:[{date_str}0000 TO {today_str}2359]"
        return f"({base}) AND {date_filter}"

    @staticmethod
    def _parse(raw_xml: bytes) -> list[Paper]:
        root = ET.fromstring(raw_xml)
        papers: list[Paper] = []
        for entry in root.findall("atom:entry", _NS):
            title_el = entry.find("atom:title", _NS)
            summary_el = entry.find("atom:summary", _NS)
            id_el = entry.find("atom:id", _NS)
            published_el = entry.find("atom:published", _NS)

            title = (title_el.text or "").strip().replace("\n", " ")
            abstract = (summary_el.text or "").strip().replace("\n", " ")
            arxiv_url = (id_el.text or "").strip()
            arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else None
            year = int(published_el.text[:4]) if published_el is not None else None

            authors = [
                (a.find("atom:name", _NS).text or "").strip()
                for a in entry.findall("atom:author", _NS)
                if a.find("atom:name", _NS) is not None
            ]

            pdf_url = ""
            for link in entry.findall("atom:link", _NS):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "")
                    break

            doi_el = entry.find("arxiv:doi", _NS)
            doi = doi_el.text.strip() if doi_el is not None else None

            categories = [
                c.get("term", "")
                for c in entry.findall("atom:category", _NS)
            ]

            papers.append(Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=arxiv_url,
                pdf_url=pdf_url,
                arxiv_id=arxiv_id,
                doi=doi,
                year=year,
                keywords=categories,
            ))
        return papers
