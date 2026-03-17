"""AI-assisted academic paper collection and summarisation tools.

This sub-package provides utilities to:

* Fetch the latest papers from **arXiv** by category or keyword.
* Search papers from academic **conferences** via the DBLP API.
* Convert a paper's metadata into an **HTML web-page** with highlighted
  section summaries.
* Format references in **BibTeX** or **APA** citation styles.
* Generate section-level **summary prompts** suitable for any LLM.

Typical usage::

    from stonesoup.tools.paper_assistant import ArxivFetcher, CitationFormatter

    fetcher = ArxivFetcher(categories=["cs.CV", "eess.SP"], max_results=20)
    papers = fetcher.fetch()

    fmt = CitationFormatter()
    for paper in papers[:3]:
        print(fmt.to_bibtex(paper))
"""

from .arxiv import ArxivFetcher
from .conference import ConferenceFetcher
from .formatter import CitationFormatter, HtmlFormatter
from .summarizer import PaperSummarizer

__all__ = [
    "ArxivFetcher",
    "ConferenceFetcher",
    "CitationFormatter",
    "HtmlFormatter",
    "PaperSummarizer",
]
