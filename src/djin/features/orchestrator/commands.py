"""
ABOUTME: Command handlers for orchestrator operations.
ABOUTME: Registers CLI commands for task overview, work summary, and time registration.
"""

import logging
from datetime import datetime
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from djin.cli.commands import register_command
from djin.common.errors import DjinError, handle_error
from djin.features.orchestrator.agent import CUSTOMERS, OrchestratorAgent

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


def _parse_customer(arg: str) -> str | None:
    """Return the normalized customer name if arg is a valid customer code, else None."""
    upper = arg.upper()
    return upper if upper in CUSTOMERS else None


def work_summary_command(args: List[str]) -> bool:
    """Generate a summary of tasks worked on for a specific date and customer."""
    try:
        date_str = None
        customer = None
        display_date = "today"
        remaining = list(args) if args else []

        # Parse date if first arg looks like YYYY-MM-DD
        if remaining and len(remaining[0]) == 10 and remaining[0][4] == "-" and remaining[0][7] == "-":
            try:
                datetime.strptime(remaining[0], "%Y-%m-%d")
                date_str = remaining.pop(0)
                display_date = date_str
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
                return False

        # Parse customer
        if remaining:
            customer = _parse_customer(remaining[0])
            if customer:
                remaining.pop(0)
            else:
                console.print(
                    f"[red]Unknown customer '{remaining[0]}'. "
                    f"Valid customers: {', '.join(CUSTOMERS.keys())}[/red]"
                )
                return False

        if not customer:
            console.print(
                f"[red]Customer is required. Valid customers: {', '.join(CUSTOMERS.keys())}[/red]"
            )
            return False

        console.print(f"[cyan]Generating work summary for {customer} on {display_date}...[/cyan]")
        summary_or_message = orchestrator_agent.generate_work_summary(date_str, customer=customer)

        if "No tasks found" in summary_or_message:
            console.print(f"[yellow]{summary_or_message}[/yellow]")
        else:
            console.print(Panel(summary_or_message, title=f"Work Summary - {customer} ({display_date})", border_style="blue"))

        return True
    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in work-summary command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred while generating the work summary.[/bold red]")
        return False


def register_time_command(args: List[str]) -> bool:
    """Register time with an auto-generated work summary.

    Usage: /register-time [YYYY-MM-DD] <AION|LG> [hours]
    """
    try:
        date_str = None
        customer = None
        hours = 8.0
        remaining = list(args) if args else []

        # Parse date if first arg looks like YYYY-MM-DD
        if remaining and len(remaining[0]) == 10 and remaining[0][4] == "-" and remaining[0][7] == "-":
            try:
                datetime.strptime(remaining[0], "%Y-%m-%d")
                date_str = remaining.pop(0)
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
                return False

        # Parse customer (required)
        if remaining:
            customer = _parse_customer(remaining[0])
            if customer:
                remaining.pop(0)
            else:
                # Check if it's a number (hours without customer)
                try:
                    float(remaining[0])
                    # It's a number, customer is missing
                except ValueError:
                    console.print(
                        f"[red]Unknown customer '{remaining[0]}'. "
                        f"Valid customers: {', '.join(CUSTOMERS.keys())}[/red]"
                    )
                    return False

        if not customer:
            console.print(
                f"[red]Customer is required. "
                f"Usage: /register-time [YYYY-MM-DD] <{'|'.join(CUSTOMERS.keys())}> [hours][/red]"
            )
            return False

        # Parse hours
        if remaining:
            try:
                hours = float(remaining[0])
            except ValueError:
                console.print(f"[yellow]Invalid hours value '{remaining[0]}', using default (8.0)[/yellow]")

        display_date = date_str or "today"
        console.print(
            f"[cyan]Registering {hours} hours for {customer} on {display_date} "
            f"with auto-generated summary...[/cyan]"
        )

        result = orchestrator_agent.register_time_with_summary(date_str, hours, customer=customer)

        if result["success"]:
            console.print(
                Panel(
                    f"[green]Successfully registered {hours} hours for {customer} on {display_date}[/green]\n\n"
                    f"[cyan]Summary:[/cyan] {result['summary']}",
                    title="Time Registration Successful",
                    border_style="green",
                )
            )
            return True
        else:
            if "No tasks found" in result.get("summary", ""):
                console.print(
                    f"[yellow]{result.get('error', 'No tasks found for this date.')}\n"
                    f"Please verify the date or register hours manually.[/yellow]"
                )
            else:
                error_msg = result.get("error", "Unknown error during registration")
                console.print(
                    Panel(
                        f"[red]Registration failed: {error_msg}[/red]\n\n"
                        f"[cyan]Generated summary:[/cyan] {result.get('summary', 'No summary generated')}",
                        title="Time Registration Failed",
                        border_style="red",
                    )
                )
            return False

    except DjinError as e:
        handle_error(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in register-time command: {e}", exc_info=True)
        console.print("[bold red]An unexpected error occurred while registering time.[/bold red]")
        return False


def register_orchestrator_commands():
    """Registers all commands related to the orchestrator feature."""
    # logger is defined at module level

    valid_customers = "|".join(CUSTOMERS.keys())
    commands_to_register = {
        "overview": (overview_command, "Show an overview of your tasks"),
        "work-summary": (
            work_summary_command,
            f"Generate a work summary (Usage: /work-summary [YYYY-MM-DD] <{valid_customers}>)",
        ),
        "register-time": (
            register_time_command,
            f"Register time with auto-generated summary (Usage: /register-time [YYYY-MM-DD] <{valid_customers}> [hours])",
        ),
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Orchestrator commands registered: {list(commands_to_register.keys())}")
