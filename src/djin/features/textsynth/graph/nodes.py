"""
Nodes for text synthesis workflows.

This module provides nodes for text synthesis workflows.
"""

import logging

from djin.features.textsynth.llm.client import TextSynthLLMClient

# Set up logging
logger = logging.getLogger("djin.textsynth.graph")


def prepare_titles_node(state):
    """
    Prepare titles for summarization.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Format titles for processing
        titles = state.titles
        if not titles:
            return state.model_copy(update={"error": "No titles provided for summarization"})

        # Log the titles being processed
        logger.info(f"Processing {len(titles)} titles for summarization")

        return state
    except Exception as e:
        error_msg = f"Error preparing titles: {str(e)}"
        logger.error(error_msg)
        return state.model_copy(update={"error": error_msg})


def summarize_titles_node(state):
    """
    Summarize titles using LLM.

    Args:
        state: Current workflow state

    Returns:
        Updated state with summary
    """
    try:
        # Check for errors from previous nodes
        if state.error:
            return state

        # Get titles from state
        titles = state.titles

        # Create LLM client
        llm_client = TextSynthLLMClient()

        # Generate summary
        summary = llm_client.summarize_titles(titles)

        # Update state with summary
        return state.model_copy(update={"summary": summary})
    except Exception as e:
        error_msg = f"Error summarizing titles: {str(e)}"
        logger.error(error_msg)
        return state.model_copy(update={"error": error_msg})
