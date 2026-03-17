"""Tests for the citation and HTML formatters."""

import pytest
from stonesoup.tools.paper_assistant.models import Paper
from stonesoup.tools.paper_assistant.formatter import CitationFormatter, HtmlFormatter


@pytest.fixture()
def sample_paper():
    return Paper(
        title="Efficient Multi-Target Tracking with Deep Learning",
        authors=["Alice Smith", "Bob Jones", "Carol White"],
        abstract=(
            "We propose a novel deep-learning approach that outperforms "
            "state-of-the-art trackers on the MOT benchmark. "
            "Our method achieves real-time performance on a single GPU."
        ),
        year=2024,
        venue="FUSION",
        arxiv_id="2401.00001",
        doi="10.1109/FUSION.2024.001",
        url="https://arxiv.org/abs/2401.00001",
        pdf_url="https://arxiv.org/pdf/2401.00001",
    )


class TestCitationFormatter:
    def test_bibtex_contains_key(self, sample_paper):
        fmt = CitationFormatter()
        bib = fmt.to_bibtex(sample_paper)
        assert "Smith2024Efficient" in bib

    def test_bibtex_entry_type(self, sample_paper):
        fmt = CitationFormatter()
        bib = fmt.to_bibtex(sample_paper)
        assert bib.startswith("@inproceedings")

    def test_bibtex_article_when_no_venue(self, sample_paper):
        sample_paper.venue = ""
        fmt = CitationFormatter()
        bib = fmt.to_bibtex(sample_paper)
        assert bib.startswith("@article")

    def test_bibtex_contains_arxiv_fields(self, sample_paper):
        fmt = CitationFormatter()
        bib = fmt.to_bibtex(sample_paper)
        assert "archivePrefix" in bib
        assert "2401.00001" in bib

    def test_apa_contains_year(self, sample_paper):
        fmt = CitationFormatter()
        apa = fmt.to_apa(sample_paper)
        assert "(2024)" in apa

    def test_apa_doi(self, sample_paper):
        fmt = CitationFormatter()
        apa = fmt.to_apa(sample_paper)
        assert "https://doi.org/10.1109/FUSION.2024.001" in apa

    def test_mla_first_author_inverted(self, sample_paper):
        fmt = CitationFormatter()
        mla = fmt.to_mla(sample_paper)
        # Last name should come first
        assert "Smith, Alice" in mla

    def test_format_dispatch_bibtex(self, sample_paper):
        fmt = CitationFormatter()
        assert fmt.format(sample_paper, "bibtex") == fmt.to_bibtex(sample_paper)

    def test_format_dispatch_apa(self, sample_paper):
        fmt = CitationFormatter()
        assert fmt.format(sample_paper, "apa") == fmt.to_apa(sample_paper)

    def test_format_dispatch_mla(self, sample_paper):
        fmt = CitationFormatter()
        assert fmt.format(sample_paper, "mla") == fmt.to_mla(sample_paper)

    def test_format_unknown_style(self, sample_paper):
        fmt = CitationFormatter()
        with pytest.raises(ValueError, match="Unknown citation style"):
            fmt.format(sample_paper, "chicago")

    def test_bibtex_key_no_authors(self):
        p = Paper(title="Orphan Paper", authors=[], year=2020)
        fmt = CitationFormatter()
        bib = fmt.to_bibtex(p)
        assert "2020" in bib

    def test_apa_no_authors(self):
        p = Paper(title="No Author Paper", authors=[], year=2021)
        fmt = CitationFormatter()
        apa = fmt.to_apa(p)
        assert "No Author Paper" in apa

    def test_apa_no_date(self):
        p = Paper(title="Undated", authors=["Zara Lee"])
        fmt = CitationFormatter()
        apa = fmt.to_apa(p)
        assert "(n.d.)" in apa


class TestHtmlFormatter:
    def test_render_produces_html(self, sample_paper):
        fmt = HtmlFormatter()
        page = fmt.render([sample_paper])
        assert "<!DOCTYPE html>" in page
        assert sample_paper.title in page

    def test_highlight_key_term(self, sample_paper):
        fmt = HtmlFormatter()
        page = fmt.render([sample_paper])
        # "novel" and "outperforms" in abstract should be highlighted
        assert 'class="highlight"' in page

    def test_render_single(self, sample_paper):
        fmt = HtmlFormatter()
        page = fmt.render_single(sample_paper)
        assert sample_paper.title in page

    def test_mobile_viewport(self, sample_paper):
        fmt = HtmlFormatter()
        page = fmt.render([sample_paper])
        assert 'name="viewport"' in page

    def test_no_arxiv_id_no_link(self):
        p = Paper(title="Book Chapter", authors=["Dan Brown"], year=2022)
        fmt = HtmlFormatter()
        page = fmt.render([p])
        assert "arxiv.org" not in page

    def test_custom_highlight_terms(self, sample_paper):
        fmt = HtmlFormatter(highlight_terms=["benchmark"])
        page = fmt.render([sample_paper])
        assert 'class="highlight"' in page

    def test_bibtex_in_details(self, sample_paper):
        fmt = HtmlFormatter()
        page = fmt.render([sample_paper])
        assert "<details" in page
        assert "BibTeX" in page

    def test_paper_title_in_page_title(self):
        fmt = HtmlFormatter()
        page = fmt.render([], title="My Digest")
        assert "<title>My Digest</title>" in page
