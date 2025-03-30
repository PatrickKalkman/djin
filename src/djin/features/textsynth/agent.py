"""
Report and text synthesis agent for Djin.

This module provides an agent specialized in report generation and text synthesis.
"""

import logging
from typing import List

from djin.common.errors import DjinError
from djin.features.textsynth.graph.workflow import create_title_summarization_graph

from typing import List, Dict, Any # Added Dict, Any

from djin.common.errors import DjinError
from djin.features.textsynth.graph.workflow import create_title_summarization_graph

# Set up logging
logger = logging.getLogger("djin.textsynth")


class TextSynthAgent:
    """Agent specialized in text synthesis operations like summarization."""

    def __init__(self):
        """Initialize the text synthesis agent."""
        # Only initialize what's needed for the remaining methods
        self._title_summarization_graph = create_title_summarization_graph()

    def summarize_titles_with_keys(self, keys: List[str], titles: List[str]) -> str:
        """
        Summarize multiple Jira issue titles, including their keys, using a LangGraph workflow.

        Args:
            keys: List of Jira issue keys.
            titles: List of corresponding Jira issue titles.

        Returns:
            str: Summarized text including ticket IDs.

        Raises:
            DjinError: If the summarization fails.
        """
        if len(keys) != len(titles):
            raise DjinError("Number of keys and titles must match for summarization.")

        try:
            logger.info(f"Summarizing {len(titles)} Jira issues (keys and titles)")

            # Use the workflow graph, passing both keys and titles
            initial_state = {"keys": keys, "titles": titles}
            result = self._title_summarization_graph.invoke(initial_state)

            # Check for errors
            if result.get("error"):
                raise DjinError(result["error"])

            # Return the summary
            return result.get("summary", "")
        except Exception as e:
            raise DjinError(f"Failed to summarize titles: {str(e)}")
