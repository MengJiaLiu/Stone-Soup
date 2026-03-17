"""Tests for the ConferenceFetcher using mocked HTTP responses."""

import json
from unittest.mock import MagicMock, patch

import pytest

from stonesoup.tools.paper_assistant.conference import ConferenceFetcher

_SAMPLE_DBLP = json.dumps({
    "result": {
        "hits": {
            "hit": [
                {
                    "info": {
                        "title": "Multi-Object Tracking at CVPR.",
                        "authors": {
                            "author": [
                                {"text": "Alice Smith"},
                                {"text": "Bob Jones"},
                            ]
                        },
                        "year": "2024",
                        "venue": "CVPR",
                        "url": "https://dblp.org/rec/conf/cvpr/SmithJ24",
                        "doi": "10.1109/CVPR.2024.001",
                    }
                }
            ]
        }
    }
}).encode()


def _mock_urlopen(url):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=_SAMPLE_DBLP)
    return cm


def test_conference_fetcher_search():
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        fetcher = ConferenceFetcher(venues=["CVPR"], keywords=["tracking"])
        papers = fetcher.search()
    assert len(papers) == 1
    p = papers[0]
    assert "Multi-Object Tracking" in p.title
    assert p.venue == "CVPR"
    assert p.year == 2024
    assert p.doi == "10.1109/CVPR.2024.001"


def test_conference_fetcher_deduplication():
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        fetcher = ConferenceFetcher(venues=["CVPR", "ECCV"], keywords=["tracking"])
        papers = fetcher.search()
    # Both venues return the same paper title → should be deduplicated to 1
    assert len(papers) == 1


def test_conference_fetcher_requires_venues_or_keywords():
    with pytest.raises(ValueError, match="Supply at least one"):
        ConferenceFetcher()


def test_conference_fetcher_keywords_only():
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        fetcher = ConferenceFetcher(keywords=["tracking"])
        papers = fetcher.search()
    assert len(papers) == 1


def test_conference_fetcher_year_in_query():
    fetcher = ConferenceFetcher(venues=["CVPR"], keywords=["tracking"], year=2024)
    queries = fetcher._build_queries()
    assert all("2024" in q for q in queries)


def test_conference_fetcher_single_author_dict():
    single_author_response = json.dumps({
        "result": {
            "hits": {
                "hit": [
                    {
                        "info": {
                            "title": "Single Author Paper",
                            "authors": {
                                "author": {"text": "Zara Lee"}
                            },
                            "year": "2023",
                            "venue": "FUSION",
                            "url": "https://example.com",
                        }
                    }
                ]
            }
        }
    }).encode()

    def _single_mock(url):
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cm)
        cm.__exit__ = MagicMock(return_value=False)
        cm.read = MagicMock(return_value=single_author_response)
        return cm

    with patch("urllib.request.urlopen", side_effect=_single_mock):
        fetcher = ConferenceFetcher(venues=["FUSION"], keywords=["tracking"])
        papers = fetcher.search()
    assert papers[0].authors == ["Zara Lee"]
