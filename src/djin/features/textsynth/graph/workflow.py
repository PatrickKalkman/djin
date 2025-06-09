"""
Workflows for text synthesis.

This module provides workflows for text synthesis operations.
"""

from langgraph.graph import StateGraph

from djin.features.textsynth.graph.nodes import prepare_titles_node, summarize_titles_node
from djin.features.textsynth.graph.state import SummarizeTitlesState


def create_title_summarization_graph():
    """
    Create a graph for summarizing Jira issue titles.

    Returns:
        StateGraph: The workflow graph
    """
    # NIBBLE: remove the comment
    # Create a new graph
    graph = StateGraph(SummarizeTitlesState)

    # NIBBLE: remove the comment
    # Add nodes
    graph.add_node("prepare_titles", prepare_titles_node)
    graph.add_node("summarize_titles", summarize_titles_node)

    # NIBBLE: remove the comment
    # Add edges
    graph.add_edge("prepare_titles", "summarize_titles")

    # NIBBLE: remove the comment
    # Set entry point
    graph.set_entry_point("prepare_titles")

    # NIBBLE: remove the comment
    # Compile the graph
    return graph.compile()
