"""
Command handlers for Jira task management.
"""

from rich.console import Console

from djin.cli.commands import register_command
from djin.common.errors import handle_error
from djin.features.tasks.agent import TaskAgent
from djin.features.tasks.jira_client import JiraError

# Create console for rich output
console = Console()
# Create task agent
task_agent = TaskAgent()


def todo_command(args):
    """Show Jira issues in To Do status."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api

        # Get the tasks API
        tasks_api = get_tasks_api()

        # Call the API method to get todo tasks - returns pre-formatted output
        result = tasks_api.get_todo_tasks()

        # Just return the result without printing it again
        # The result is already a formatted string with the table
        return result
    except Exception as e:
        console.print(f"[red]Error showing To Do issues: {str(e)}[/red]")
        return False


def active_command(args):
    """Show all active Jira issues."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api

        # Get the tasks API
        tasks_api = get_tasks_api()

        # Call the API method to get active tasks
        result = tasks_api.get_active_tasks()

        # Return the result
        return result
    except Exception as e:
        console.print(f"[red]Error showing active issues: {str(e)}[/red]")
        return False


def worked_on_command(args):
    """Show Jira issues worked on for a specific date."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api
        import logging

        logger = logging.getLogger("djin.tasks")
        
        # Get the tasks API
        tasks_api = get_tasks_api()
        
        # Parse date argument if provided
        date_str = None  # Default to today
        if args and len(args) > 0:
            date_str = args[0]
            # Validate date format
            from datetime import datetime
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD format.[/red]")
                return False

        # Log that we're fetching worked-on tasks
        display_date = date_str or "today"
        logger.info(f"Fetching tasks worked on for {display_date}")
        console.print(f"[cyan]Searching for tasks worked on {display_date}...[/cyan]")
        
        # Call the API method to get tasks worked on
        result = tasks_api.get_worked_on_tasks(date_str)

        # Return the result
        return result
    except Exception as e:
        console.print(f"[red]Error showing worked on issues: {str(e)}[/red]")
        return False


def completed_command(args):
    """Show completed Jira issues."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api

        # Get the tasks API
        tasks_api = get_tasks_api()

        # Parse days argument if provided
        days = 7  # Default
        if args and len(args) > 0:
            try:
                days = int(args[0])
            except ValueError:
                console.print("[yellow]Invalid days value, using default (7)[/yellow]")

        # Call the API method to get completed tasks
        result = tasks_api.get_completed_tasks(days)

        # Return the result
        return result
    except Exception as e:
        console.print(f"[red]Error showing completed issues: {str(e)}[/red]")
        return False


def task_details_command(args):
    """Show details for a specific Jira issue."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api

        # Get the tasks API
        tasks_api = get_tasks_api()

        # Check if issue key is provided
        if not args or len(args) == 0:
            console.print("[red]Error: Please provide a Jira issue key (e.g., /tasks PROJ-123)[/red]")
            return False

        # Get the issue key from args
        issue_key = args[0]

        # Call the API method to get task details
        result = tasks_api.get_task_details(issue_key)

        # Return the result
        return result
    except Exception as e:
        console.print(f"[red]Error showing task details: {str(e)}[/red]")
        return False


def set_task_status_command(args):
    """Transition a Jira issue to a new status."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api

        # Get the tasks API
        tasks_api = get_tasks_api()

        # Check arguments
        if len(args) < 2:
            console.print(
                "[red]Error: Please provide a Jira issue key and the target status (e.g., /tasks set-status PROJ-123 'In Progress')[/red]"
            )
            return False  # Indicate command failure

        issue_key = args[0]
        # Join remaining args in case status has spaces (e.g., "In Progress")
        status_name = " ".join(args[1:])

        # Call the API method to set task status
        result = tasks_api.set_task_status(issue_key, status_name)

        # The result is already printed by the agent, no need to print it again
        # Determine success based on the result string (simple check)
        return "[green]" in result

    except Exception as e:
        # Catch unexpected errors during API call or argument parsing
        handle_error(JiraError(f"An unexpected error occurred in the command: {str(e)}"))
        return False  # Indicate command failure


register_command(
    "tasks todo",
    todo_command,
    "Show your Jira issues in To Do status",
)

register_command(
    "tasks active",
    active_command,
    "Show all your active Jira issues",
)

register_command(
    "tasks worked-on",
    worked_on_command,
    "Show Jira issues you worked on for a specific date (default: today)",
)

register_command(
    "tasks completed",
    completed_command,
    "Show your completed Jira issues (default: last 7 days)",
)

register_command(
    "tasks",
    task_details_command,
    "Show details for a specific Jira issue (e.g., /tasks PROJ-123)",
)

register_command(
    "tasks set-status",
    set_task_status_command,
    "Set the status of a Jira issue (e.g., /tasks set-status PROJ-123 'In Progress')",
)
