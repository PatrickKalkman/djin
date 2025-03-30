"""
Public API for the report and text synthesis agent.

This module provides a public interface for other agents to call the report and text synthesis agent.
"""

from typing import List

from typing import List, Dict, Any # Added Dict, Any

from djin.features.textsynth.agent import TextSynthAgent


class TextSynthAPI:
    """Public API for the text synthesis agent."""

    def __init__(self):
        """Initialize the text synth API with a text synthesis agent."""
        self._agent = TextSynthAgent()

    def summarize_tasks(self, tasks_data: List[Dict[str, Any]]) -> str:
        """
        Summarize multiple Jira issues based on their keys and titles.

        Args:
            tasks_data: List of dictionaries, each containing 'key' and 'summary'.

        Returns:
            str: Summarized text including ticket IDs.
        """
        # Extract keys and titles for the agent
        keys = [task.get("key") for task in tasks_data]
        titles = [task.get("summary") for task in tasks_data]
        return self._agent.summarize_titles_with_keys(keys, titles) # Renamed agent method
