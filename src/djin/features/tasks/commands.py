"""
Command handlers for Jira task management.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from djin.cli.commands import register_command
from djin.features.tasks.agent import TaskAgent
from djin.features.tasks.jira_client import create_jira_link, display_issues

# Create console for rich output
console = Console()
# Create task agent
task_agent = TaskAgent()


def completed_command(args):
    """Show completed Jira issues."""
    try:
        # Default to 7 days if no argument provided
        days = 7

        # Parse days argument if provided
        if args and args[0].isdigit():
            days = int(args[0])

        # Get completed tasks using the agent
        tasks = task_agent.get_completed_tasks(days=days)

        # Convert tasks back to Jira issues for display
        # This is temporary until we refactor display_issues to work with our new models
        from djin.features.tasks.jira_client import get_my_completed_issues

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

        # Get active tasks using the agent
        tasks = task_agent.get_active_tasks()

        # Convert tasks back to Jira issues for display
        # This is temporary until we refactor display_issues to work with our new models
        from djin.features.tasks.jira_client import get_my_issues

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
        # Get task details using the agent
        details = task_agent.get_task_details(issue_key)

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


def todo_command(args):
    """Show Jira issues in To Do status."""
    try:
        # Use the API layer to get the tasks agent
        from djin.features.tasks.api import get_tasks_api
        
        # Get the tasks API
        tasks_api = get_tasks_api()
        
        # Call the API method to get todo tasks
        result = tasks_api.get_todo_tasks()
        
        # Print the result (already formatted for display)
        console.print(result)
        
        return True
    except Exception as e:
        console.print(f"[red]Error showing To Do issues: {str(e)}[/red]")
        return False


def summarize_command(args):
    """Generate a summary of tasks using LLM."""
    try:
        from djin.features.tasks.llm.client import TaskLLMClient

        # Create LLM client
        llm_client = TaskLLMClient()

        # Get active and completed tasks
        active_tasks = task_agent.get_active_tasks()
        completed_tasks = task_agent.get_completed_tasks(days=7)

        # Generate report
        report = llm_client.generate_task_report(active_tasks, completed_tasks)

        # Display report
        console.print(Panel(report, title="Task Summary", border_style="green"))

        return True
    except Exception as e:
        console.print(f"[red]Error generating task summary: {str(e)}[/red]")
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

register_command(
    "tasks todo",
    todo_command,
    "Show your Jira issues in To Do status",
)

register_command(
    "tasks summarize",
    summarize_command,
    "Generate a summary of your tasks using AI",
)
