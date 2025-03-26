"""
Command handlers for Jira task management.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from djin.cli.commands import register_command
from djin.features.tasks.jira_client import (
    create_jira_link,
    display_issues,
    get_issue_details,
    get_my_completed_issues,
)

# Create console for rich output
console = Console()


def completed_command(args):
    """Show completed Jira issues."""
    try:
        # Default to 7 days if no argument provided
        days = 7

        # Parse days argument if provided
        if args and args[0].isdigit():
            days = int(args[0])

        # Get completed issues
        issues = get_my_completed_issues(days=days)

        # Display issues
        display_issues(issues, title=f"My Completed Issues (Last {days} Days)")

        return True
    except Exception as e:
        console.print(f"[red]Error showing completed issues: {str(e)}[/red]")
        return False


def tasks_command(args):
    """Show active Jira issues that are not in To Do, Done, or Resolved status."""
    try:
        # If an issue key is provided, show details for that issue
        if args and len(args) == 1 and "-" in args[0]:
            return show_issue_details(args[0])
            
        from djin.features.tasks.jira_client import get_my_issues
        
        # Get only issues that are active (not to do, done, or resolved)
        status_filter = "status != 'To Do' AND status != 'Done' AND status != 'Resolved'"
        issues = get_my_issues(status_filter=status_filter)
        
        # Display issues
        display_issues(issues, title="My Active Issues")
        
        return True
    except Exception as e:
        console.print(f"[red]Error showing active issues: {str(e)}[/red]")
        return False


def show_issue_details(issue_key):
    """Show detailed information about a specific Jira issue."""
    try:
        # Get issue details
        details = get_issue_details(issue_key)
        
        # Create a table for the issue details
        table = Table(title=f"Issue Details: {create_jira_link(issue_key)}")
        
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        
        # Add rows for each field
        table.add_row("Summary", details["summary"])
        table.add_row("Status", details["status"])
        table.add_row("Type", details["type"])
        table.add_row("Priority", details["priority"])
        table.add_row("Assignee", details["assignee"])
        table.add_row("Reporter", details["reporter"])
        table.add_row("Created", details["created"])
        table.add_row("Updated", details["updated"])
        table.add_row("Time Spent", details.get("worklog_formatted", ""))
        
        if "due_date" in details:
            table.add_row("Due Date", details["due_date"])
        
        console.print(table)
        
        # Show description in a panel if it exists
        if details["description"]:
            console.print(Panel(details["description"], title="Description", border_style="cyan"))
        
        return True
    except Exception as e:
        console.print(f"[red]Error showing issue details: {str(e)}[/red]")
        return False


# Register task commands
register_command(
    "tasks completed",
    completed_command,
    "Show your completed Jira issues. Optional: specify number of days to look back (default: 7)",
)

register_command(
    "tasks",
    tasks_command,
    "Show your active Jira issues (not To Do, Done, or Resolved)",
)

register_command(
    "tasks <KEY>",
    tasks_command,
    "Show details for Jira issue <KEY>",
)
