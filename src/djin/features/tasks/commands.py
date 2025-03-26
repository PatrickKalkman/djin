"""
Command handlers for Jira task management.
"""

from rich.console import Console

from djin.cli.commands import register_command
from djin.features.tasks.jira_client import display_issues, get_my_completed_issues

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
