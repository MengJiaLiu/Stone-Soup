"""Tests for the paper_assistant models module."""

from stonesoup.tools.paper_assistant.models import Paper


def test_paper_defaults():
    p = Paper(title="Test Paper", authors=["Alice Smith", "Bob Jones"])
    assert p.abstract == ""
    assert p.url == ""
    assert p.pdf_url == ""
    assert p.arxiv_id is None
    assert p.doi is None
    assert p.year is None
    assert p.venue == ""
    assert p.keywords == []


def test_paper_short_title_short():
    p = Paper(title="Short Title", authors=[])
    assert p.short_title == "Short Title"


def test_paper_short_title_long():
    long_title = "A" * 70
    p = Paper(title=long_title, authors=[])
    assert len(p.short_title) == 60
    assert p.short_title.endswith("...")
