"""
Command handlers for Jira task management.
"""

from rich.console import Console

from djin.cli.commands import register_command
from djin.features.tasks.agent import TaskAgent

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

        return True
    except Exception as e:
        console.print(f"[red]Error showing To Do issues: {str(e)}[/red]")
        return False


register_command(
    "tasks todo",
    todo_command,
    "Show your Jira issues in To Do status",
)
