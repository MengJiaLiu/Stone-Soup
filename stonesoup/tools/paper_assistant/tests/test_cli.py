"""Tests for the paper_assistant CLI."""

import json
import textwrap
from unittest.mock import MagicMock, patch

from stonesoup.tools.paper_assistant.cli import main

_SAMPLE_ATOM = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>https://arxiv.org/abs/2401.99999v1</id>
        <title>CLI Test Paper</title>
        <summary>Novel approach to target tracking in real-time.</summary>
        <published>2024-01-20T00:00:00Z</published>
        <author><name>Test Author</name></author>
        <link type="application/pdf"
              href="https://arxiv.org/pdf/2401.99999"/>
        <category term="eess.SP"/>
      </entry>
    </feed>
""").encode()

_SAMPLE_DBLP = json.dumps({
    "result": {
        "hits": {
            "hit": [
                {
                    "info": {
                        "title": "Tracking in FUSION",
                        "authors": {"author": [{"text": "Jane Doe"}]},
                        "year": "2024",
                        "venue": "FUSION",
                        "url": "https://dblp.org/rec/conf/fusion/Doe24",
                    }
                }
            ]
        }
    }
}).encode()


def _arxiv_mock(url):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=_SAMPLE_ATOM)
    return cm


def _dblp_mock(url):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=_SAMPLE_DBLP)
    return cm


def test_arxiv_plain_text(capsys):
    with patch("urllib.request.urlopen", side_effect=_arxiv_mock):
        main(["arxiv", "--categories", "eess.SP"])
    captured = capsys.readouterr()
    assert "CLI Test Paper" in captured.out


def test_arxiv_bibtex(capsys):
    with patch("urllib.request.urlopen", side_effect=_arxiv_mock):
        main(["arxiv", "--categories", "eess.SP", "--cite", "bibtex"])
    captured = capsys.readouterr()
    assert "@" in captured.out


def test_arxiv_apa(capsys):
    with patch("urllib.request.urlopen", side_effect=_arxiv_mock):
        main(["arxiv", "--categories", "eess.SP", "--cite", "apa"])
    captured = capsys.readouterr()
    assert "CLI Test Paper" in captured.out


def test_arxiv_prompts(capsys):
    with patch("urllib.request.urlopen", side_effect=_arxiv_mock):
        main(["arxiv", "--categories", "eess.SP", "--prompts"])
    captured = capsys.readouterr()
    assert "TL;DR" in captured.out


def test_arxiv_html_output(tmp_path):
    out_file = tmp_path / "digest.html"
    with patch("urllib.request.urlopen", side_effect=_arxiv_mock):
        main(["arxiv", "--categories", "eess.SP", "--html", str(out_file)])
    content = out_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "CLI Test Paper" in content


def test_conference_plain_text(capsys):
    with patch("urllib.request.urlopen", side_effect=_dblp_mock):
        main(["conference", "--venues", "FUSION", "--keywords", "tracking"])
    captured = capsys.readouterr()
    assert "Tracking in FUSION" in captured.out


def test_conference_bibtex(capsys):
    with patch("urllib.request.urlopen", side_effect=_dblp_mock):
        main(["conference", "--venues", "FUSION", "--keywords", "tracking",
              "--cite", "bibtex"])
    captured = capsys.readouterr()
    assert "@" in captured.out
