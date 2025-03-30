"""
Report and text synthesis agent for Djin.

This module provides an agent specialized in report generation and text synthesis.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from djin.common.errors import DjinError
from djin.features.tasks.api import TaskAPI
from djin.features.textsynth.graph.workflow import create_title_summarization_graph
# Removed unused imports: datetime, timedelta, TaskAPI, ReportLLMClient

# Set up logging
logger = logging.getLogger("djin.textsynth")


class TextSynthAgent:
    """Agent specialized in text synthesis operations like summarization."""

    def __init__(self):
        """Initialize the text synthesis agent."""
        # Only initialize what's needed for the remaining methods
        self._title_summarization_graph = create_title_summarization_graph()

    def summarize_titles(self, titles: List[str]) -> str:
        """
        Summarize multiple Jira issue titles using a LangGraph workflow.
        
        Args:
            titles: List of Jira issue titles
            
        Returns:
            str: Summarized text
            
        Raises:
            DjinError: If the summarization fails
        """
        try:
            logger.info(f"Summarizing {len(titles)} Jira issue titles")
            
            # Use the workflow graph
            result = self._title_summarization_graph.invoke({"titles": titles})
            
            # Check for errors
            if result.get("error"):
                raise DjinError(result["error"])
                
            # Return the summary
            return result.get("summary", "")
        except Exception as e:
            raise DjinError(f"Failed to summarize titles: {str(e)}")
