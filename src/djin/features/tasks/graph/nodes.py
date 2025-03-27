"""
Node definitions for task workflows.

This module provides node functions for LangGraph workflows.
"""

from djin.features.tasks.display import format_tasks_table
from djin.features.tasks.jira_client import get_my_issues, get_my_completed_issues


# Node for fetching tasks
def fetch_tasks_node(state):
    """Fetch tasks from Jira"""
    try:
        # Fetch based on request type
        if state.request_type == "todo":
            status_filter = "status = 'To Do'"
            raw_tasks = get_my_issues(status_filter=status_filter)
        elif state.request_type == "in_progress":
            status_filter = "status = 'In Progress'"
            raw_tasks = get_my_issues(status_filter=status_filter)
        elif state.request_type == "completed":
            days = getattr(state, "days", 7)
            raw_tasks = get_my_completed_issues(days=days)
        else:
            raw_tasks = get_my_issues()

        return {"raw_tasks": raw_tasks}
    except Exception as e:
        return {"errors": state.errors + [f"Error fetching tasks: {str(e)}"]}


# Node for processing tasks
def process_tasks_node(state):
    """Process the raw tasks using LLM if needed"""
    # For simple todo listing, we might not need LLM processing
    # But this node allows for more complex processing in the future
    processed_tasks = []
    for issue in state.raw_tasks:
        processed_tasks.append(
            {
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "type": issue.fields.issuetype.name,
                "priority": getattr(issue.fields.priority, "name", "Unknown"),
                "assignee": getattr(issue.fields.assignee, "displayName", "Unassigned")
                if hasattr(issue.fields, "assignee")
                else "Unassigned",
                "worklog_seconds": getattr(issue, "worklog_seconds", 0),
            }
        )
    return {"processed_tasks": processed_tasks}


# Node for formatting output
def format_output_node(state):
    """Format the tasks for display"""
    from rich.console import Console

    # Format the tasks as a table with appropriate title based on request type
    title = "My Tasks"
    if state.request_type == "todo":
        title = "My To Do Tasks"
    elif state.request_type == "in_progress":
        title = "My In Progress Tasks"
    elif state.request_type == "completed":
        title = f"My Completed Tasks (Last {state.days} Days)"
    
    table = format_tasks_table(state.processed_tasks, title=title)

    # Capture the output as a string
    console = Console(record=True)
    console.print(table)

    return {"formatted_output": console.export_text()}
