"""
Workflow definitions for task operations.

This module provides LangGraph workflow definitions for task operations.
"""

from langgraph.graph import StateGraph

from djin.features.tasks.graph.nodes import fetch_tasks_node, format_output_node, process_tasks_node
from djin.features.tasks.graph.state import TaskState


def create_task_fetching_graph():
    """Create a graph for fetching and processing tasks"""
    # Create a new state graph
    workflow = StateGraph(TaskState)

    # Add nodes
    workflow.add_node("fetch_tasks", fetch_tasks_node)
    workflow.add_node("process_tasks", process_tasks_node)
    workflow.add_node("format_output", format_output_node)

    # Define the flow
    workflow.add_edge("fetch_tasks", "process_tasks")
    workflow.add_edge("process_tasks", "format_output")

    # Compile the graph
    return workflow.compile()
