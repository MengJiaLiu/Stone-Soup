"""Format paper metadata as citations or self-contained HTML pages.

Two public classes are exposed:

* :class:`CitationFormatter` – produce BibTeX or APA citation strings.
* :class:`HtmlFormatter` – render a paper (or a list of papers) as an HTML
  web page with highlighted abstract sections.

Example
-------
>>> from stonesoup.tools.paper_assistant.models import Paper
>>> from stonesoup.tools.paper_assistant.formatter import CitationFormatter
>>> p = Paper(
...     title="A Survey of Tracking Algorithms",
...     authors=["Alice Smith", "Bob Jones"],
...     year=2024,
...     venue="FUSION",
...     arxiv_id="2401.00001",
...     doi="10.1234/fusion.2024.001",
... )
>>> bib = CitationFormatter().to_bibtex(p)
>>> "Smith2024" in bib
True
"""

from __future__ import annotations

import html
import re
import textwrap
from typing import Optional

from .models import Paper


# ---------------------------------------------------------------------------
# Citation formatter
# ---------------------------------------------------------------------------


class CitationFormatter:
    """Convert :class:`~.Paper` metadata to citation strings.

    Supported styles
    ----------------
    * ``"bibtex"`` — BibTeX ``@article`` / ``@inproceedings`` entry.
    * ``"apa"``    — APA 7th-edition formatted string.
    * ``"mla"``    — MLA 9th-edition formatted string.
    """

    def format(self, paper: Paper, style: str = "bibtex") -> str:
        """Return a formatted citation string.

        Parameters
        ----------
        paper:
            The paper to format.
        style:
            One of ``"bibtex"``, ``"apa"``, or ``"mla"`` (case-insensitive).
        """
        style = style.lower()
        if style == "bibtex":
            return self.to_bibtex(paper)
        elif style == "apa":
            return self.to_apa(paper)
        elif style == "mla":
            return self.to_mla(paper)
        else:
            raise ValueError(f"Unknown citation style '{style}'. "
                             "Choose from: bibtex, apa, mla.")

    # ------------------------------------------------------------------

    def to_bibtex(self, paper: Paper) -> str:
        """Return a BibTeX entry string for *paper*."""
        key = self._bibtex_key(paper)
        entry_type = "inproceedings" if paper.venue else "article"
        lines = [f"@{entry_type}{{{key},"]
        lines.append(f"  title     = {{{{{paper.title}}}}},")
        authors_str = " and ".join(paper.authors)
        lines.append(f"  author    = {{{authors_str}}},")
        if paper.year:
            lines.append(f"  year      = {{{paper.year}}},")
        if paper.venue:
            lines.append(f"  booktitle = {{{paper.venue}}},")
        if paper.doi:
            lines.append(f"  doi       = {{{paper.doi}}},")
        if paper.arxiv_id:
            lines.append("  archivePrefix = {arXiv},")
            lines.append(f"  eprint    = {{{paper.arxiv_id}}},")
        if paper.url:
            lines.append(f"  url       = {{{paper.url}}},")
        lines.append("}")
        return "\n".join(lines)

    def to_apa(self, paper: Paper) -> str:
        """Return an APA 7th-edition formatted citation string."""
        authors_str = self._apa_authors(paper.authors)
        year = f"({paper.year})" if paper.year else "(n.d.)"
        title = paper.title
        venue = f" *{paper.venue}*." if paper.venue else "."
        doi_part = f" https://doi.org/{paper.doi}" if paper.doi else (
            f" {paper.url}" if paper.url else "")
        return f"{authors_str} {year}. {title}.{venue}{doi_part}"

    def to_mla(self, paper: Paper) -> str:
        """Return an MLA 9th-edition formatted citation string."""
        if paper.authors:
            first = paper.authors[0]
            parts = first.rsplit(" ", 1)
            if len(parts) == 2:
                first_mla = f"{parts[1]}, {parts[0]}"
            else:
                first_mla = first
            if len(paper.authors) > 1:
                author_str = f"{first_mla}, et al."
            else:
                author_str = f"{first_mla}."
        else:
            author_str = ""
        title = f'"{paper.title}."'
        venue = f" *{paper.venue}*," if paper.venue else ""
        year = f" {paper.year}," if paper.year else ""
        doi_part = (
            f" https://doi.org/{paper.doi}." if paper.doi
            else (f" {paper.url}." if paper.url else "")
        )
        return f"{author_str} {title}{venue}{year}{doi_part}".strip()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _bibtex_key(paper: Paper) -> str:
        first_author_last = ""
        if paper.authors:
            name = paper.authors[0]
            first_author_last = name.split()[-1] if name.split() else name
        first_author_last = re.sub(r"[^A-Za-z]", "", first_author_last)
        year = str(paper.year) if paper.year else "XXXX"
        first_word = re.sub(r"[^A-Za-z]", "", paper.title.split()[0]) if paper.title else "Paper"
        return f"{first_author_last}{year}{first_word}"

    @staticmethod
    def _apa_authors(authors: list[str]) -> str:
        if not authors:
            return ""
        formatted: list[str] = []
        for name in authors[:20]:
            parts = name.rsplit(" ", 1)
            if len(parts) == 2:
                formatted.append(f"{parts[1]}, {parts[0][0]}.")
            else:
                formatted.append(name)
        if len(authors) > 20:
            return ", ".join(formatted[:19]) + ", ... " + formatted[-1]
        return ", ".join(formatted)


# ---------------------------------------------------------------------------
# HTML formatter
# ---------------------------------------------------------------------------


class HtmlFormatter:
    """Render papers as self-contained HTML pages.

    The generated page includes:

    * A styled paper card for each paper with title, authors, year and venue.
    * The abstract rendered with automatic **highlight spans** around
      sentences that contain key tracking/signal-processing terms.
    * A "copy citation" button pre-populated with the BibTeX entry.
    * Mobile-responsive CSS (single ``<style>`` block, no external deps).

    Parameters
    ----------
    highlight_terms:
        Extra terms to highlight in addition to the built-in list.
    """

    _DEFAULT_TERMS = [
        "novel", "state-of-the-art", "outperform", "propose", "introduce",
        "demonstrate", "achieve", "significantly", "improved", "efficient",
        "real-time", "robust", "accurate", "benchmark", "sota",
    ]

    def __init__(self, highlight_terms: Optional[list[str]] = None) -> None:
        self._terms = self._DEFAULT_TERMS + (highlight_terms or [])

    # ------------------------------------------------------------------

    def render(self, papers: list[Paper], title: str = "Paper Digest") -> str:
        """Return a full HTML document for *papers*.

        Parameters
        ----------
        papers:
            Papers to include in the page.
        title:
            ``<title>`` and ``<h1>`` heading for the page.
        """
        cards = "\n".join(self._paper_card(p) for p in papers)
        return self._page(title, cards)

    def render_single(self, paper: Paper) -> str:
        """Return a full HTML document for a single *paper*."""
        return self.render([paper], title=paper.title)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _highlight_abstract(self, abstract: str) -> str:
        """Wrap key sentences with a ``<mark>`` element."""
        sentences = re.split(r"(?<=[.!?])\s+", abstract)
        result: list[str] = []
        for sent in sentences:
            lower = sent.lower()
            if any(t in lower for t in self._terms):
                result.append(f'<mark class="highlight">{html.escape(sent)}</mark>')
            else:
                result.append(html.escape(sent))
        return " ".join(result)

    def _paper_card(self, paper: Paper) -> str:
        cit = CitationFormatter().to_bibtex(paper)
        cit_escaped = html.escape(cit)
        abstract_html = self._highlight_abstract(paper.abstract) if paper.abstract else ""
        venue_badge = (
            f'<span class="venue-badge">{html.escape(paper.venue)}</span> '
            if paper.venue else ""
        )
        year_span = (
            f'<span class="year">{paper.year}</span>' if paper.year else ""
        )
        authors_html = html.escape(", ".join(paper.authors[:5]))
        if len(paper.authors) > 5:
            authors_html += " <em>et al.</em>"
        arxiv_link = ""
        if paper.arxiv_id:
            arxiv_link = (
                f'<a href="https://arxiv.org/abs/{html.escape(paper.arxiv_id)}" '
                f'target="_blank" rel="noopener">arXiv:{html.escape(paper.arxiv_id)}</a>'
            )
        pdf_link = ""
        if paper.pdf_url:
            pdf_link = (
                f' &middot; <a href="{html.escape(paper.pdf_url)}" '
                f'target="_blank" rel="noopener">PDF</a>'
            )

        return textwrap.dedent(f"""\
            <article class="paper-card">
              <h2 class="paper-title">{html.escape(paper.title)}</h2>
              <p class="paper-meta">{venue_badge}{year_span} &middot; {authors_html}</p>
              <p class="paper-links">{arxiv_link}{pdf_link}</p>
              <p class="paper-abstract">{abstract_html}</p>
              <details class="citation-block">
                <summary>BibTeX</summary>
                <pre><code>{cit_escaped}</code></pre>
              </details>
            </article>""")

    @staticmethod
    def _page(title: str, body: str) -> str:
        escaped_title = html.escape(title)
        return textwrap.dedent(f"""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>{escaped_title}</title>
              <style>
                :root {{
                  --accent: #2563eb;
                  --bg: #f8fafc;
                  --card-bg: #ffffff;
                  --text: #1e293b;
                  --muted: #64748b;
                  --highlight-bg: #fef9c3;
                  --highlight-border: #fbbf24;
                }}
                @media (prefers-color-scheme: dark) {{
                  :root {{
                    --bg: #0f172a; --card-bg: #1e293b; --text: #e2e8f0;
                    --muted: #94a3b8; --highlight-bg: #422006; --highlight-border: #d97706;
                  }}
                }}
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{ font-family: system-ui, sans-serif; background: var(--bg);
                        color: var(--text); padding: 1rem; }}
                h1 {{ font-size: 1.5rem; margin-bottom: 1.5rem; }}
                .paper-card {{ background: var(--card-bg); border-radius: 0.75rem;
                               padding: 1.25rem; margin-bottom: 1rem;
                               box-shadow: 0 1px 3px rgba(0,0,0,.12); }}
                .paper-title {{ font-size: 1.05rem; color: var(--accent);
                                margin-bottom: .5rem; }}
                .paper-meta {{ font-size: .85rem; color: var(--muted);
                               margin-bottom: .4rem; }}
                .venue-badge {{ background: var(--accent); color: #fff;
                                padding: .1rem .4rem; border-radius: .25rem;
                                font-size: .75rem; margin-right: .25rem; }}
                .paper-links {{ font-size: .85rem; margin-bottom: .6rem; }}
                .paper-links a {{ color: var(--accent); text-decoration: none; }}
                .paper-abstract {{ font-size: .9rem; line-height: 1.6; }}
                mark.highlight {{
                  background: var(--highlight-bg);
                  border-left: 3px solid var(--highlight-border);
                  padding: 0 .15rem; border-radius: .15rem;
                }}
                .citation-block {{ margin-top: .75rem; }}
                .citation-block summary {{ cursor: pointer; font-size: .85rem;
                                           color: var(--muted); }}
                .citation-block pre {{ background: var(--bg); padding: .75rem;
                                       border-radius: .5rem; overflow-x: auto;
                                       font-size: .78rem; margin-top: .5rem; }}
                @media (max-width: 600px) {{
                  body {{ padding: .5rem; }}
                  .paper-card {{ padding: 1rem; }}
                }}
              </style>
            </head>
            <body>
              <h1>{escaped_title}</h1>
              {body}
            </body>
            </html>""")
