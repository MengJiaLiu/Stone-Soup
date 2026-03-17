"""Generate structured LLM prompts for paper summarisation.

This module does **not** call any external AI service.  Instead it produces
well-structured prompts that a user can paste into any LLM (Claude, GPT-4,
Gemini, …) to obtain:

* A section-by-section summary of the paper.
* Key contributions highlighted in bullet form.
* Suggested citation placement relative to the user's own work.
* A daily reading-plan schedule.

Example
-------
>>> from stonesoup.tools.paper_assistant.models import Paper
>>> from stonesoup.tools.paper_assistant.summarizer import PaperSummarizer
>>> p = Paper(title="Kalman Filter Survey", authors=["Alice"],
...           abstract="We survey Kalman filter variants.", year=2024)
>>> prompt = PaperSummarizer().section_summary_prompt(p)
>>> "Kalman Filter Survey" in prompt
True
"""

from __future__ import annotations

import textwrap
from typing import Optional

from .models import Paper


class PaperSummarizer:
    """Generate LLM prompts for structured paper analysis.

    Parameters
    ----------
    user_topic:
        Short description of the user's own research topic.  Used to
        personalise the citation-placement prompt.
    """

    def __init__(self, user_topic: str = "target tracking and state estimation") -> None:
        self.user_topic = user_topic

    # ------------------------------------------------------------------
    # Public prompts
    # ------------------------------------------------------------------

    def section_summary_prompt(self, paper: Paper) -> str:
        """Return a prompt that asks an LLM to summarise each section.

        The prompt instructs the LLM to produce a structured digest with:
        * One-sentence TL;DR
        * Introduction summary
        * Methods/Approach summary
        * Results summary
        * Limitations
        * Three key takeaways
        """
        abstract_block = (
            f"\nAbstract:\n{textwrap.fill(paper.abstract, 80)}\n"
            if paper.abstract else ""
        )
        return textwrap.dedent(f"""\
            You are an expert academic researcher. Analyse the following paper and
            produce a structured digest.

            Title: {paper.title}
            Authors: {", ".join(paper.authors)}
            Year: {paper.year or "unknown"}{abstract_block}
            ---
            Please provide:
            1. **TL;DR** (one sentence)
            2. **Introduction** – What problem does this paper address and why
               does it matter?
            3. **Methods / Approach** – Describe the key technical approach or
               algorithm proposed.
            4. **Results** – What are the main empirical results or theoretical
               contributions?
            5. **Limitations** – What are the stated or implied limitations?
            6. **Key takeaways** – Three bullet points a researcher in
               "{self.user_topic}" should remember.

            Format your response using Markdown headings.
            """)

    def citation_placement_prompt(self, paper: Paper,
                                  own_abstract: Optional[str] = None) -> str:
        """Return a prompt asking an LLM where to cite *paper* in the user's work.

        Parameters
        ----------
        paper:
            The candidate reference.
        own_abstract:
            The user's own paper abstract for context.
        """
        own_block = (
            f"\nMy paper abstract:\n{textwrap.fill(own_abstract, 80)}\n"
            if own_abstract else ""
        )
        return textwrap.dedent(f"""\
            I am writing a research paper on "{self.user_topic}". {own_block}
            I have found the following related work:

            Title: {paper.title}
            Authors: {", ".join(paper.authors)}
            Year: {paper.year or "unknown"}
            Abstract: {textwrap.fill(paper.abstract, 80)}

            Please suggest:
            1. **Relationship** – How does this paper relate to my research topic?
            2. **Where to cite** – Which section(s) of my paper should reference
               this work (e.g. Related Work, Introduction, Experiments)?
            3. **Citation sentence** – Write one or two example sentences I could
               use to introduce this citation in context.
            """)

    def daily_plan_prompt(self, papers: list[Paper],
                          days_available: int = 5) -> str:
        """Return a prompt asking an LLM to create a reading schedule.

        Parameters
        ----------
        papers:
            Papers to schedule.
        days_available:
            Number of days over which to spread the reading.
        """
        paper_list = "\n".join(
            f"  {i + 1}. {p.title} ({p.year or 'n.d.'})"
            for i, p in enumerate(papers)
        )
        return textwrap.dedent(f"""\
            I have {len(papers)} papers to read over the next {days_available} days.
            My research topic is "{self.user_topic}".

            Papers:
            {paper_list}

            Please create a day-by-day reading plan that:
            1. Prioritises papers most relevant to "{self.user_topic}".
            2. Groups related papers on the same day where possible.
            3. Leaves time each day for note-taking and reflection.
            4. Provides a short note on what to focus on for each paper.

            Format as a numbered daily schedule.
            """)

    def key_contributions_prompt(self, paper: Paper) -> str:
        """Return a prompt asking an LLM to extract key contributions."""
        return textwrap.dedent(f"""\
            Extract the key contributions of the following paper as a concise
            bullet-point list (maximum 6 bullets).

            Title: {paper.title}
            Abstract: {textwrap.fill(paper.abstract, 80)}

            Each bullet should start with an action verb (e.g. Proposes, Introduces,
            Demonstrates, Proves, Shows, Reduces).
            """)
