"""
Display utilities for tasks.

This module provides functions for formatting and displaying tasks.
"""

from rich.table import Table
from rich.text import Text

from djin.common.config import load_config
from djin.features.tasks.jira_client import format_time_spent


def create_jira_link(issue_key: str) -> Text:
    """
    Create a clickable hyperlink for a JIRA issue key.

    Args:
        issue_key: The JIRA issue key (e.g., PROJ-1234)

    Returns:
        Text: A Rich Text object with a hyperlink that's clickable in compatible terminals
    """
    # Get Jira URL from config
    config = load_config()
    jira_url = config.get("jira", {}).get("url", "")

    # Create browse URL
    if jira_url:
        if not jira_url.endswith("/"):
            jira_url += "/"
        browse_url = f"{jira_url}browse/{issue_key}"
    else:
        # Fallback to a generic format if URL not configured
        browse_url = f"https://jira.atlassian.net/browse/{issue_key}"

    # Create a Rich Text object with a hyperlink
    text = Text(issue_key)
    text.stylize(f"link {browse_url}")
    return text


def format_tasks_table(tasks, title="Tasks"):
    """
    Format tasks as a Rich table.

    Args:
        tasks: List of task dictionaries
        title: Title for the table

    Returns:
        Table: A Rich Table object
    """
    if not tasks:
        table = Table(title=f"{title} (0 total)")
        table.add_column("Message")
        table.add_row("No tasks found")
        return table

    # Create table
    table = Table(title=f"{title} ({len(tasks)} total)")

    # Add columns
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary")
    table.add_column("Status", style="green", no_wrap=True)
    table.add_column("Priority", no_wrap=True)
    table.add_column("Time Spent", style="yellow", no_wrap=True)

    # Add rows
    for task in tasks:
        # Format time spent
        time_spent = format_time_spent(task.get("worklog_seconds", 0))

        # Add row with clickable issue key
        table.add_row(
            create_jira_link(task["key"]),
            task["summary"],
            task["status"],
            task.get("priority", "Unknown"),
            time_spent,
        )

    return table


def format_task_details(task_details):
    """
    Format detailed information about a task.
    
    Args:
        task_details: Dictionary containing task details
        
    Returns:
        Table: A Rich Table object with detailed task information
    """
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.markdown import Markdown
    from datetime import datetime
    
    # Create a panel for the task
    title = f"{task_details['key']}: {task_details['summary']}"
    
    # Create a table for the details
    details_table = Table(show_header=False, box=None)
    details_table.add_column("Field", style="bold cyan")
    details_table.add_column("Value")
    
    # Add basic details
    details_table.add_row("Status", task_details['status'])
    details_table.add_row("Type", task_details['type'])
    details_table.add_row("Priority", task_details.get('priority', 'Unknown'))
    details_table.add_row("Assignee", task_details.get('assignee', 'Unassigned'))
    details_table.add_row("Reporter", task_details.get('reporter', 'Unknown'))
    
    # Format dates
    if 'created' in task_details:
        created_date = task_details['created']
        if isinstance(created_date, str):
            # Parse ISO format date
            try:
                created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                details_table.add_row("Created", created_date.strftime("%Y-%m-%d %H:%M"))
            except ValueError:
                details_table.add_row("Created", created_date)
        else:
            details_table.add_row("Created", str(created_date))
    
    if 'updated' in task_details:
        updated_date = task_details['updated']
        if isinstance(updated_date, str):
            try:
                updated_date = datetime.fromisoformat(updated_date.replace('Z', '+00:00'))
                details_table.add_row("Updated", updated_date.strftime("%Y-%m-%d %H:%M"))
            except ValueError:
                details_table.add_row("Updated", updated_date)
        else:
            details_table.add_row("Updated", str(updated_date))
    
    if 'due_date' in task_details:
        details_table.add_row("Due Date", task_details['due_date'])
    
    # Add time tracking info
    if 'worklog_formatted' in task_details:
        details_table.add_row("Time Spent", task_details['worklog_formatted'])
    elif 'worklog_seconds' in task_details:
        details_table.add_row("Time Spent", format_time_spent(task_details['worklog_seconds']))
    
    # Create a panel for the description if it exists
    description_panel = None
    if task_details.get('description'):
        description_text = task_details['description']
        # Try to render as markdown, fall back to plain text if it fails
        try:
            description_content = Markdown(description_text)
            description_panel = Panel(description_content, title="Description", border_style="blue")
        except Exception:
            description_panel = Panel(Text(description_text), title="Description", border_style="blue")
    
    # Create the main panel
    main_panel = Panel(
        details_table,
        title=title,
        border_style="green",
        expand=False
    )
    
    # Return a table that contains both panels
    result_table = Table(show_header=False, box=None, expand=True)
    result_table.add_column("Content", ratio=1)
    result_table.add_row(main_panel)
    
    if description_panel:
        result_table.add_row(description_panel)
    
    return result_table
