"""
Public API for the report and text synthesis agent.

This module provides a public interface for other agents to call the report and text synthesis agent.
"""

from typing import List

from djin.features.textsynth.agent import TextSynthAgent


class TextSynthAPI:
    """Public API for the text synthesis agent."""

    def __init__(self):
        """Initialize the text synth API with a text synthesis agent."""
        self._agent = TextSynthAgent()

    def summarize_titles(self, titles: List[str]) -> str:
        """
        Summarize multiple Jira issue titles.

        Args:
            titles: List of Jira issue titles

        Returns:
            str: Summarized text
        """
        return self._agent.summarize_titles(titles)
