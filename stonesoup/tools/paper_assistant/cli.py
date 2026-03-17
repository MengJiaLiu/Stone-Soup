"""Command-line interface for the Stone Soup paper assistant.

Usage
-----
Fetch today's arXiv papers in cs.CV and eess.SP::

    stonesoup-papers arxiv --categories cs.CV eess.SP

Search CVPR papers on tracking::

    stonesoup-papers conference --venues CVPR --keywords tracking

Generate an HTML digest and open it in a browser::

    stonesoup-papers arxiv --categories eess.SP --html digest.html

Print BibTeX for conference search results::

    stonesoup-papers conference --venues FUSION --keywords kalman --cite bibtex
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .arxiv import ArxivFetcher
from .conference import ConferenceFetcher
from .formatter import CitationFormatter, HtmlFormatter
from .summarizer import PaperSummarizer


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def _cmd_arxiv(args: argparse.Namespace) -> None:
    fetcher = ArxivFetcher(
        categories=args.categories or None,
        keywords=args.keywords or None,
        max_results=args.max_results,
        days_back=args.days_back,
    )
    papers = fetcher.fetch()
    _output(papers, args)


def _cmd_conference(args: argparse.Namespace) -> None:
    fetcher = ConferenceFetcher(
        venues=args.venues or None,
        keywords=args.keywords or None,
        max_results=args.max_results,
        year=args.year,
    )
    papers = fetcher.search()
    _output(papers, args)


def _output(papers, args: argparse.Namespace) -> None:  # type: ignore[type-arg]
    if not papers:
        print("No papers found.", file=sys.stderr)
        return

    if getattr(args, "html", None):
        fmt = HtmlFormatter()
        html_content = fmt.render(papers)
        out_path = Path(args.html)
        out_path.write_text(html_content, encoding="utf-8")
        print(f"HTML digest written to {out_path}")
        return

    if getattr(args, "cite", None):
        fmt = CitationFormatter()
        for paper in papers:
            print(fmt.format(paper, style=args.cite))
            print()
        return

    if getattr(args, "prompts", False):
        summarizer = PaperSummarizer(user_topic=args.topic or "target tracking")
        for paper in papers:
            print("=" * 72)
            print(summarizer.section_summary_prompt(paper))
        return

    # Default: plain-text listing
    for i, paper in enumerate(papers, 1):
        authors = ", ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors += " et al."
        year = f" ({paper.year})" if paper.year else ""
        venue = f" [{paper.venue}]" if paper.venue else ""
        print(f"{i:3}. {paper.title}{year}{venue}")
        print(f"     {authors}")
        if paper.arxiv_id:
            print(f"     https://arxiv.org/abs/{paper.arxiv_id}")
        elif paper.url:
            print(f"     {paper.url}")
        print()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stonesoup-papers",
        description="AI-assisted paper collection and summarisation tool.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- arxiv ---------------------------------------------------------------
    arxiv_p = sub.add_parser(
        "arxiv",
        help="Fetch recent papers from arXiv.",
    )
    arxiv_p.add_argument(
        "--categories", nargs="+", metavar="CAT",
        help="arXiv category codes, e.g. cs.CV eess.SP",
    )
    arxiv_p.add_argument(
        "--keywords", nargs="+", metavar="KW",
        help="Keyword search terms.",
    )
    arxiv_p.add_argument(
        "--max-results", type=int, default=20, metavar="N",
        help="Maximum number of papers to fetch (default: 20).",
    )
    arxiv_p.add_argument(
        "--days-back", type=int, default=1, metavar="D",
        help="Fetch papers from the last D days (default: 1).",
    )
    _add_output_args(arxiv_p)

    # -- conference ----------------------------------------------------------
    conf_p = sub.add_parser(
        "conference",
        help="Search conference papers via DBLP.",
    )
    conf_p.add_argument(
        "--venues", nargs="+", metavar="VENUE",
        help="Conference short names, e.g. CVPR ECCV FUSION",
    )
    conf_p.add_argument(
        "--keywords", nargs="+", metavar="KW",
        help="Keyword search terms.",
    )
    conf_p.add_argument(
        "--year", type=int, default=None,
        help="Filter by publication year.",
    )
    conf_p.add_argument(
        "--max-results", type=int, default=20, metavar="N",
        help="Maximum results per venue (default: 20).",
    )
    _add_output_args(conf_p)

    return parser


def _add_output_args(subparser: argparse.ArgumentParser) -> None:
    out_group = subparser.add_mutually_exclusive_group()
    out_group.add_argument(
        "--html", metavar="FILE",
        help="Write an HTML digest to FILE.",
    )
    out_group.add_argument(
        "--cite", choices=["bibtex", "apa", "mla"],
        help="Print citations in the chosen format.",
    )
    out_group.add_argument(
        "--prompts", action="store_true",
        help="Print LLM summarisation prompts for each paper.",
    )
    subparser.add_argument(
        "--topic", metavar="TOPIC", default="target tracking",
        help='Your research topic (used with --prompts, default: "target tracking").',
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "arxiv":
        _cmd_arxiv(args)
    elif args.command == "conference":
        _cmd_conference(args)


if __name__ == "__main__":
    main()
