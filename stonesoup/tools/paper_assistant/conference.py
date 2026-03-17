"""Search academic conference proceedings via the DBLP API.

`DBLP <https://dblp.org>`_ is a free, public computer-science bibliography
service.  No API key is required.

Example
-------
>>> from stonesoup.tools.paper_assistant.conference import ConferenceFetcher
>>> fetcher = ConferenceFetcher(venues=["CVPR"], keywords=["tracking"])
>>> papers = fetcher.search()  # returns list[Paper]
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import json
from typing import Optional

from .models import Paper

_DBLP_SEARCH = "https://dblp.org/search/publ/api"


class ConferenceFetcher:
    """Search conference papers through the DBLP bibliographic API.

    Parameters
    ----------
    venues:
        Conference short-names (e.g. ``["CVPR", "ECCV", "ICCV"]``).
        Each venue is combined with *keywords* via an AND search.
        If left empty only *keywords* are used.
    keywords:
        Topic keywords added to every query.
    max_results:
        Maximum number of results per venue (default ``20``).
    year:
        Restrict results to a specific publication year.
    """

    def __init__(
        self,
        venues: Optional[list[str]] = None,
        keywords: Optional[list[str]] = None,
        max_results: int = 20,
        year: Optional[int] = None,
    ) -> None:
        if not venues and not keywords:
            raise ValueError("Supply at least one of 'venues' or 'keywords'.")
        self.venues = venues or []
        self.keywords = keywords or []
        self.max_results = max_results
        self.year = year

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self) -> list[Paper]:
        """Run the search and return a deduplicated list of :class:`~.Paper` objects."""
        seen: set[str] = set()
        results: list[Paper] = []
        queries = self._build_queries()
        for query in queries:
            batch = self._query_dblp(query)
            for paper in batch:
                key = paper.title.lower()
                if key not in seen:
                    seen.add(key)
                    results.append(paper)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_queries(self) -> list[str]:
        kw_part = " ".join(self.keywords)
        if self.venues:
            queries = []
            for venue in self.venues:
                parts = []
                if kw_part:
                    parts.append(kw_part)
                parts.append(f"venue:{venue}")
                if self.year:
                    parts.append(str(self.year))
                queries.append(" ".join(parts))
            return queries
        parts = [kw_part]
        if self.year:
            parts.append(str(self.year))
        return [" ".join(parts)]

    def _query_dblp(self, query: str) -> list[Paper]:
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "h": self.max_results,
            "f": 0,
        })
        url = f"{_DBLP_SEARCH}?{params}"
        with urllib.request.urlopen(url) as resp:  # noqa: S310
            data = json.loads(resp.read())

        hits = (
            data.get("result", {})
                .get("hits", {})
                .get("hit", [])
        )
        papers: list[Paper] = []
        for hit in hits:
            info = hit.get("info", {})
            raw_authors = info.get("authors", {}).get("author", [])
            if isinstance(raw_authors, dict):
                raw_authors = [raw_authors]
            authors = [
                a.get("text", "") if isinstance(a, dict) else str(a)
                for a in raw_authors
            ]

            title = info.get("title", "").rstrip(".")
            url = info.get("url", "")
            doi = info.get("doi", None)
            year_str = info.get("year", None)
            year = int(year_str) if year_str else None
            venue = info.get("venue", "")

            papers.append(Paper(
                title=title,
                authors=authors,
                url=url,
                doi=doi,
                year=year,
                venue=venue,
            ))
        return papers
