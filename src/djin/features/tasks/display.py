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
