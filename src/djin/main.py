"""
Djin - A magical terminal assistant for developers.
"""

import argparse
import sys

from rich.console import Console

from djin.cli.app import main_loop
from djin.common.config import is_configured, setup_config
from djin.common.errors import handle_error
from djin.features.tasks import commands as task_commands
from djin.features.textsynth import commands as textsynth_commands
from djin.features.notes import commands as notes_commands
from djin.cli.commands import register_command

# Create console for rich output
console = Console()


def register_commands():
    """Register all commands with the command system."""
    # Register task commands
    register_command("tasks", task_commands.task_details_command, 
                    "Show details for a specific Jira issue (e.g., /tasks PROJ-123)")
    register_command("tasks todo", task_commands.todo_command, 
                    "Show your Jira issues in To Do status")
    register_command("tasks active", task_commands.active_command, 
                    "Show all your active Jira issues")
    register_command("tasks worked-on", task_commands.worked_on_command, 
                    "Show Jira issues you worked on for a specific date (default: today)")
    register_command("tasks completed", task_commands.completed_command, 
                    "Show your completed Jira issues (default: last 7 days)")
    register_command("tasks set-status", task_commands.set_task_status_command, 
                    "Set the status of a Jira issue (e.g., /tasks set-status PROJ-123 'In Progress')")
    
    # Register report/textsynth commands
    register_command("report daily", textsynth_commands.daily_report_command, 
                    "Generate a daily report of your tasks")
    register_command("report weekly", textsynth_commands.weekly_report_command, 
                    "Generate a weekly report of your tasks")
    register_command("report custom", textsynth_commands.custom_report_command, 
                    "Generate a custom report of your tasks. Optional: specify number of days to look back (default: 7)")
    register_command("summarize", textsynth_commands.summarize_titles_command, 
                    "Summarize multiple Jira issue titles. Usage: /summarize 'Title 1' 'Title 2' ...")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Djin - A magical terminal assistant for developers",
        epilog="Type '/help' within the application for more information.",
    )

    # Setup command
    parser.add_argument("--setup", action="store_true", help="Run initial setup")

    # Reset database
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset the database (WARNING: This will delete all data)",
    )

    # Backup database
    parser.add_argument("--backup-db", action="store_true", help="Create a backup of the database")

    return parser.parse_args()


def main():
    """Main entry point for Djin."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Handle setup command
        if args.setup:
            setup_config()
            console.print("[green]Setup complete! You can now run Djin.[/green]")
            return 0

        # Check if configured
        if not is_configured():
            console.print("[yellow]Djin is not configured yet. Running setup...[/yellow]")
            setup_config()
            
        # Register all commands
        register_commands()

        # Start the main application loop
        main_loop()

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return 0
    except Exception as e:
        handle_error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
