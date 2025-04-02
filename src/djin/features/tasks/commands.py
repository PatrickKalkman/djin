"""
Command handlers for Jira task management.
"""

from datetime import datetime
from typing import List

from loguru import logger
from rich.console import Console

from djin.cli.commands import register_command
from djin.common.errors import DjinError, handle_error
from djin.features.tasks.display import format_tasks_table
from djin.features.tasks.jira_client import JiraError

console = Console()


def _handle_task_list_result(result_dict: dict, title: str) -> bool:
    """Helper to display task list results or errors."""
    tasks = result_dict.get("tasks", [])
    errors = result_dict.get("errors", [])

    if errors:
        for error in errors:
            if "No tasks found that you worked on" in error:
                console.print(f"[yellow]{error}[/yellow]")
            else:
                console.print(f"[red]Error: {error}[/red]")
        if not tasks and any("No tasks found that you worked on" not in e for e in errors):
            return False

    if tasks:
        table = format_tasks_table(tasks, title=title)
        console.print(table)
        return True
    elif not errors:
        console.print(f"[yellow]No tasks found for '{title}'.[/yellow]")
        return True

    if any("No tasks found that you worked on" in e for e in errors):
        return True

    return False


def todo_command(args: List[str]) -> bool:
    """Show Jira issues in To Do status."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()
        result_dict = tasks_api.get_todo_tasks()
        return _handle_task_list_result(result_dict, "My To Do Tasks")
    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in todo command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred.[/bold red]")
        return False


def active_command(args: List[str]) -> bool:
    """Show all active Jira issues."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()
        result_dict = tasks_api.get_active_tasks()
        return _handle_task_list_result(result_dict, "My Active Tasks")
    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in active command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred.[/bold red]")
        return False


def worked_on_command(args: List[str]) -> bool:
    """Show Jira issues worked on for a specific date."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()

        date_str = None
        display_date = "today"
        if args and len(args) > 0:
            date_str = args[0]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_str
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD format.[/red]")
                return False

        logger.info(f"Command: Fetching tasks worked on for {display_date}")
        console.print(f"[cyan]Searching for tasks worked on {display_date}...[/cyan]")

        result_dict = tasks_api.get_worked_on_tasks(date_str)
        return _handle_task_list_result(result_dict, f"Tasks Worked On ({display_date})")

    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in worked-on command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred.[/bold red]")
        return False


def completed_command(args: List[str]) -> bool:
    """Show completed Jira issues."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()

        days = 7
        if args and len(args) > 0:
            try:
                days = int(args[0])
            except ValueError:
                console.print("[yellow]Invalid days value, using default (7)[/yellow]")

        result_dict = tasks_api.get_completed_tasks(days)
        return _handle_task_list_result(result_dict, f"My Completed Tasks (Last {days} Days)")
    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in completed command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred.[/bold red]")
        return False


def task_details_command(args: List[str]) -> bool:
    """Show details for a specific Jira issue."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()

        if not args or len(args) == 0:
            console.print("[red]Error: Please provide a Jira issue key (e.g., /tasks PROJ-123)[/red]")
            return False

        issue_key = args[0]
        result_output = tasks_api.get_task_details(issue_key)

        return not result_output.strip().startswith("[red]")

    except DjinError as e:
        # Handle Djin specific errors if the API call itself fails before returning string
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in task-details command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred.[/bold red]")
        return False


def set_task_status_command(args: List[str]) -> bool:
    """Transition a Jira issue to a new status."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()

        if len(args) < 2:
            console.print(
                "[red]Error: Please provide a Jira issue key and the target status (e.g., /tasks set-status PROJ-123 'In Progress')[/red]"
            )
            return False

        issue_key = args[0]
        status_name = " ".join(args[1:])

        result_output = tasks_api.set_task_status(issue_key, status_name)

        console.print(result_output)
        return "[green]" in result_output

    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in set-status command: {e}", exc_info=True)
        handle_error(JiraError(f"An unexpected error occurred in the command: {str(e)}"))
        return False


def create_ticket_command(args: List[str]) -> bool:
    """Create a new Jira ticket in the AION MEDIA GROUP project."""
    try:
        from djin.features.tasks.api import get_tasks_api

        tasks_api = get_tasks_api()

        if not args or len(args) < 2:
            console.print(
                "[red]Error: Please provide a summary and description for the ticket.[/red]"
            )
            console.print("[yellow]Usage: /tasks create \"Summary here\" \"Description here\"[/yellow]")
            return False

        summary = args[0]
        description = " ".join(args[1:]) if len(args) > 1 else ""

        console.print("[cyan]Creating new ticket in AION MEDIA GROUP project...[/cyan]")
        result_output = tasks_api.create_ticket(summary, description)
        
        console.print(result_output)
        return "[green]" in result_output

    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in create-ticket command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred.[/bold red]")
        return False


def register_task_commands():
    """Registers all commands related to the tasks feature."""
    commands_to_register = {
        "tasks todo": (todo_command, "Show your Jira issues in To Do status"),
        "tasks active": (active_command, "Show all your active Jira issues"),
        "tasks worked-on": (
            worked_on_command,
            "Show Jira issues you worked on for a specific date (YYYY-MM-DD, default: today)",
        ),
        "tasks completed": (
            completed_command,
            "Show your completed Jira issues (default: last 7 days)",
        ),
        "tasks": (
            task_details_command,
            "Show details for a specific Jira issue (e.g., /tasks PROJ-123)",
        ),
        "tasks set-status": (
            set_task_status_command,
            "Set the status of a Jira issue (e.g., /tasks set-status PROJ-123 'In Progress')",
        ),
        "tasks create": (
            create_ticket_command,
            "Create a new Jira ticket in AION MEDIA GROUP (e.g., /tasks create \"Summary\" \"Description\")",
        ),
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Task commands registered: {list(commands_to_register.keys())}")
