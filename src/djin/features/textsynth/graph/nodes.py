"""
Nodes for text synthesis workflows.

This module provides nodes for text synthesis workflows.
"""

import logging
from typing import Any, Dict

from djin.features.textsynth.llm.client import ReportLLMClient

# Set up logging
logger = logging.getLogger("djin.textsynth.graph")


def prepare_titles_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare titles for summarization.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Format titles for processing
        titles = state.get("titles", [])
        if not titles:
            state = state.copy(update={"error": "No titles provided for summarization"})
            return state

        # Log the titles being processed
        logger.info(f"Processing {len(titles)} titles for summarization")

        return state
    except Exception as e:
        state = state.copy(update={"error": f"Error preparing titles: {str(e)}"})
        logger.error(state["error"])
        return state


def summarize_titles_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize titles using LLM.

    Args:
        state: Current workflow state

    Returns:
        Updated state with summary
    """
    try:
        # Check for errors from previous nodes
        if state.get("error"):
            return state

        # Get titles from state
        titles = state.get("titles", [])

        # Create LLM client
        llm_client = ReportLLMClient()

        # Generate summary
        summary = llm_client.summarize_titles(titles)

        # Update state with summary
        state = state.copy(update={"summary": summary})

        return state
    except Exception as e:
        state = state.copy(update={"error": f"Error summarizing titles: {str(e)}"})
        logger.error(state["error"])
        return state
