"""
Node definitions for task workflows.

This module provides node functions for LangGraph workflows.
"""

from djin.features.tasks.display import format_tasks_table
from djin.features.tasks.jira_client import get_my_completed_issues, get_my_issues


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
        elif state.request_type == "task_details":
            # For task details, we'll put the result in raw_tasks even though it's a single item
            from djin.features.tasks.jira_client import get_issue_details
            issue_key = getattr(state, "issue_key", "")
            if not issue_key:
                return {"errors": state.errors + ["No issue key provided"]}
            task_details = get_issue_details(issue_key)
            raw_tasks = [task_details]  # Wrap in list to maintain consistent structure
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
    
    # Handle task_details differently since it's already a dictionary
    if state.request_type == "task_details" and state.raw_tasks:
        # The task details are already processed by get_issue_details
        processed_tasks = state.raw_tasks
    else:
        # Process regular Jira issue objects
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

    # Capture the output as a string
    console = Console(record=True)
    
    # Handle task details differently
    if state.request_type == "task_details":
        from djin.features.tasks.display import format_task_details
        if state.processed_tasks:
            # Format the single task details
            task_details = format_task_details(state.processed_tasks[0])
            console.print(task_details)
        else:
            console.print(f"[red]No details found for issue {state.issue_key}[/red]")
    else:
        # Format the tasks as a table with appropriate title based on request type
        title = "My Tasks"
        if state.request_type == "todo":
            title = "My To Do Tasks"
        elif state.request_type == "in_progress":
            title = "My In Progress Tasks"
        elif state.request_type == "completed":
            title = f"My Completed Tasks (Last {state.days} Days)"

        table = format_tasks_table(state.processed_tasks, title=title)
        console.print(table)

    return {"formatted_output": console.export_text()}
