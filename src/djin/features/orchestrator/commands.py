"""
Command handlers for orchestrator operations.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from djin.cli.commands import register_command
from djin.features.orchestrator.agent import OrchestratorAgent

# Create console for rich output
console = Console()
# Create orchestrator agent
orchestrator_agent = OrchestratorAgent()


def overview_command(args):
    """Show an overview of tasks."""
    try:
        # Get task overview
        overview = orchestrator_agent.get_task_overview()

        # Create table for overview
        table = Table(title="Task Overview")

        table.add_column("Metric", style="cyan")
        table.add_column("Value")

        # Add rows for each metric
        table.add_row("Active Tasks", str(overview["active_count"]))
        table.add_row("To Do Tasks", str(overview["todo_count"]))
        table.add_row("Completed Tasks (Last 7 Days)", str(overview["completed_count"]))

        # Format time spent
        hours, remainder = divmod(overview["total_time_spent"], 3600)
        minutes, _ = divmod(remainder, 60)
        time_spent = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        table.add_row("Total Time Spent", time_spent)

        # Display table
        console.print(table)

        return True
    except Exception as e:
        console.print(f"[red]Error showing task overview: {str(e)}[/red]")
        return False


def summarize_command(args):
    """Generate a summary of tasks."""
    try:
        # Default to 7 days if no argument provided
        days = 7

        # Parse days argument if provided
        if args and args[0].isdigit():
            days = int(args[0])

        # Generate task summary
        summary = orchestrator_agent.generate_task_summary(days=days)

        # Display summary
        console.print(Panel(summary, title=f"Task Summary (Last {days} Days)", border_style="green"))

        return True
    except Exception as e:
        console.print(f"[red]Error generating task summary: {str(e)}[/red]")
        return False


def register_orchestrator_commands():
    """Registers all commands related to the orchestrator feature."""
    import logging  # Import logging here or at the top level

    logger = logging.getLogger("djin.orchestrator.commands")

    commands_to_register = {
        "overview": (overview_command, "Show an overview of your tasks"),
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Orchestrator commands registered: {list(commands_to_register.keys())}")
