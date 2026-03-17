"""Tests for the ArxivFetcher using mocked HTTP responses."""

import textwrap
from unittest.mock import MagicMock, patch

import pytest

from stonesoup.tools.paper_assistant.arxiv import ArxivFetcher

_SAMPLE_ATOM = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>https://arxiv.org/abs/2401.00001v1</id>
        <title>Test Paper Title</title>
        <summary>This is a test abstract for the test paper.</summary>
        <published>2024-01-15T00:00:00Z</published>
        <author><name>Alice Smith</name></author>
        <author><name>Bob Jones</name></author>
        <link type="application/pdf"
              href="https://arxiv.org/pdf/2401.00001"/>
        <category term="cs.CV"/>
        <category term="eess.SP"/>
        <arxiv:doi>10.1234/test.001</arxiv:doi>
      </entry>
    </feed>
""").encode()


def _mock_urlopen(url):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=_SAMPLE_ATOM)
    return cm


def test_fetch_returns_paper():
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        fetcher = ArxivFetcher(categories=["cs.CV"], max_results=5)
        papers = fetcher.fetch()
    assert len(papers) == 1
    p = papers[0]
    assert p.title == "Test Paper Title"
    assert p.authors == ["Alice Smith", "Bob Jones"]
    assert p.year == 2024
    assert p.arxiv_id == "2401.00001v1"
    assert p.doi == "10.1234/test.001"
    assert "cs.CV" in p.keywords


def test_fetch_pdf_url():
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        fetcher = ArxivFetcher(categories=["cs.CV"])
        papers = fetcher.fetch()
    assert papers[0].pdf_url == "https://arxiv.org/pdf/2401.00001"


def test_arxiv_fetcher_requires_categories_or_keywords():
    with pytest.raises(ValueError, match="Supply at least one"):
        ArxivFetcher()


def test_arxiv_fetcher_keywords_only():
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        fetcher = ArxivFetcher(keywords=["tracking"], max_results=3)
        papers = fetcher.fetch()
    assert len(papers) == 1


def test_build_query_with_both():
    fetcher = ArxivFetcher(categories=["cs.CV"], keywords=["tracking"])
    query = fetcher._build_query()
    assert "cat:cs.CV" in query
    assert "all:tracking" in query
