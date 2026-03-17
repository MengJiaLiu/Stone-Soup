"""Tests for the PaperSummarizer prompt builder."""

import pytest
from stonesoup.tools.paper_assistant.models import Paper
from stonesoup.tools.paper_assistant.summarizer import PaperSummarizer


@pytest.fixture()
def paper():
    return Paper(
        title="Kalman Filter Variants for Non-Linear Tracking",
        authors=["Eve Turner", "Frank Müller"],
        abstract="We survey extended and unscented Kalman filter variants.",
        year=2023,
        venue="FUSION",
    )


def test_section_summary_prompt_contains_title(paper):
    s = PaperSummarizer()
    prompt = s.section_summary_prompt(paper)
    assert paper.title in prompt


def test_section_summary_prompt_contains_tldr(paper):
    s = PaperSummarizer()
    prompt = s.section_summary_prompt(paper)
    assert "TL;DR" in prompt


def test_section_summary_prompt_contains_user_topic(paper):
    topic = "multi-sensor fusion"
    s = PaperSummarizer(user_topic=topic)
    prompt = s.section_summary_prompt(paper)
    assert topic in prompt


def test_citation_placement_prompt_contains_title(paper):
    s = PaperSummarizer()
    prompt = s.citation_placement_prompt(paper)
    assert paper.title in prompt


def test_citation_placement_prompt_with_own_abstract(paper):
    s = PaperSummarizer()
    prompt = s.citation_placement_prompt(
        paper, own_abstract="I study particle filter methods."
    )
    assert "I study particle filter methods." in prompt


def test_daily_plan_prompt_contains_paper_titles(paper):
    papers = [paper, Paper(title="Another Paper", authors=["Grace"], year=2024)]
    s = PaperSummarizer()
    prompt = s.daily_plan_prompt(papers, days_available=3)
    assert paper.title in prompt
    assert "Another Paper" in prompt
    assert "3" in prompt


def test_key_contributions_prompt(paper):
    s = PaperSummarizer()
    prompt = s.key_contributions_prompt(paper)
    assert paper.title in prompt
    assert "bullet" in prompt.lower()
