"""
Command handlers for orchestrator operations.
"""

import logging  # Added import
from datetime import datetime  # Added import
from typing import List  # Added import

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from djin.cli.commands import register_command
from djin.common.errors import DjinError, handle_error  # Added imports
from djin.features.orchestrator.agent import OrchestratorAgent

# Create console and agent
console = Console()
orchestrator_agent = OrchestratorAgent()
logger = logging.getLogger("djin.orchestrator.commands")  # Define logger at module level


def overview_command(args: List[str]) -> bool:
    """Show an overview of tasks."""
    try:
        console.print("[cyan]Fetching task overview...[/cyan]")
        overview = orchestrator_agent.get_task_overview()

        table = Table(title="Task Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")  # Changed style for visibility

        # Add rows for each metric
        table.add_row("Active Tasks", str(overview.get("active_count", "N/A")))
        table.add_row("To Do Tasks", str(overview.get("todo_count", "N/A")))
        table.add_row("Completed (Last 7 Days)", str(overview.get("completed_count", "N/A")))

        # Format time spent safely
        total_seconds = overview.get("total_time_spent", 0)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        time_spent = f"{int(hours)}h {int(minutes)}m" if hours > 0 else f"{int(minutes)}m"
        table.add_row("Total Time Spent (Active/Completed)", time_spent)

        console.print(table)
        return True
    except DjinError as e:
        # Handle errors raised by the agent (e.g., failed task fetching)
        handle_error(e)
        return False
    except Exception as e:
        # Handle unexpected errors in the command itself
        logger.error(f"Unexpected error in overview command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred while fetching the overview.[/bold red]")
        return False


def work_summary_command(args: List[str]) -> bool:
    """Generate a summary of tasks worked on for a specific date."""
    try:
        date_str = None
        display_date = "today"
        if args and len(args) > 0:
            date_str = args[0]
            try:
                # Validate date format
                datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_str
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
                return False  # Indicate command failure due to bad input

        console.print(f"[cyan]Generating work summary for {display_date}...[/cyan]")
        # Agent method now returns the summary string or an info/error message string
        summary_or_message = orchestrator_agent.generate_work_summary(date_str)

        # Display the result in a panel, whether it's a summary or a message
        if "No tasks found" in summary_or_message:
            # Display info message without a panel title suggesting a summary was generated
            console.print(f"[yellow]{summary_or_message}[/yellow]")
        else:
            # Display the generated summary
            console.print(Panel(summary_or_message, title=f"Work Summary ({display_date})", border_style="blue"))

        # Command succeeded if no exceptions were raised
        return True
    except DjinError as e:
        # Handle errors raised by the agent (e.g., failed task fetching or summarization)
        handle_error(e)
        return False  # Indicate command failure
    except Exception as e:
        # Handle unexpected errors in the command itself
        logger.error(f"Unexpected error in work-summary command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred while generating the work summary.[/bold red]")
        return False  # Indicate command failure


def register_orchestrator_commands():
    """Registers all commands related to the orchestrator feature."""
    # logger is defined at module level

    commands_to_register = {
        "overview": (overview_command, "Show an overview of your tasks"),
        "work-summary": (
            work_summary_command,
            "Generate a summary of tasks worked on for a date (YYYY-MM-DD, default: today)",
        ),
        # Removed the old "summarize" command as its agent logic was removed/unclear
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Orchestrator commands registered: {list(commands_to_register.keys())}")
