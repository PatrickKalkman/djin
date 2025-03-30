"""
Workflow definitions for accounting operations.
"""
import logging

from langgraph.graph import END, StateGraph

from djin.features.accounting.graph.nodes import (
    format_output_node,
    register_hours_node,
    validate_input_node,
)
from djin.features.accounting.graph.state import RegisterHoursState

logger = logging.getLogger("djin.accounting.workflow")


def create_register_hours_graph():
    """Create a graph for registering hours."""
    workflow = StateGraph(RegisterHoursState)

    # Add nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("register_hours", register_hours_node)
    workflow.add_node("format_output", format_output_node)

    # Define edges
    workflow.set_entry_point("validate_input")

    # Conditional edge after validation
    workflow.add_conditional_edges(
        "validate_input",
        # Function to decide the next step based on validation_errors
        lambda state: "format_output" if state.validation_errors else "register_hours",
        {
            "register_hours": "register_hours", # If no validation errors, proceed to register
            "format_output": "format_output",   # If validation errors, go directly to format output
        }
    )

    workflow.add_edge("register_hours", "format_output")
    workflow.add_edge("format_output", END) # End after formatting output

    logger.info("Register hours graph created.")
    return workflow.compile()
