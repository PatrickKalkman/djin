"""
Main CLI application loop for Djin.
"""

import logging
import pathlib
import shlex  # Import shlex for robust splitting
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from djin.__version__ import __version__ as VERSION

# Import the command router and core command registration (if you create one)
from djin.cli.commands import exit_command, help_command, register_command, route_command

# Import the registration functions from feature modules
from djin.features.accounting.commands import register_accounting_commands # Added import
from djin.features.notes.commands import add_note_command, register_note_commands

# Import database initialization if you want to do it once at startup
from djin.features.notes.db.schema import init_database as init_notes_db
from djin.features.orchestrator.commands import register_orchestrator_commands
from djin.features.tasks.commands import register_task_commands
from djin.features.textsynth.commands import register_textsynth_commands

# Import other feature command registration functions here as you create them

# Import other initializers if needed

# Create console for rich output
console = Console()
logger = logging.getLogger("djin.cli.app")  # Added logger

# Style for the prompt
style = Style.from_dict(
    {
        "prompt": "#00FFFF",  # Cyan color for the prompt
    }
)


def display_welcome():
    """Display welcome message."""
    welcome_text = Text()
    welcome_text.append("Welcome to ", style="white")
    welcome_text.append("Djin", style="bright_cyan")
    welcome_text.append(f" v{VERSION}", style="bright_cyan")
    welcome_text.append(" - Your magical terminal assistant!", style="white")

    panel = Panel(welcome_text, title=f"✨ Djin v{VERSION}", border_style="cyan")
    console.print(panel)
    console.print("Type /help for available commands.")


def process_command(command_string: str):
    """Process a slash command using shlex for robust parsing."""
    logger.debug(f"Processing command string: '{command_string}'")
    # Remove the leading slash and split using shlex
    try:
        cmd_parts = shlex.split(command_string[1:])
        logger.debug(f"Command parts after shlex split: {cmd_parts}")
    except ValueError as e:
        logger.error(f"Error parsing command string: {e}")
        console.print(f"[red]Error parsing command: {e}[/red]")
        return

    if not cmd_parts:
        logger.warning("Empty command received after stripping slash.")
        console.print("[red]Error: Empty command[/red]")
        return

    # The first part is the potential command or start of a multi-word command
    cmd_name = cmd_parts[0].lower()
    args = cmd_parts[1:]  # All subsequent parts are arguments

    logger.debug(f"Attempting to route command: '{cmd_name}' with args: {args}")

    # Use the command router from commands.py
    # route_command will handle checking for subcommands (e.g., "tasks todo")
    result = route_command(cmd_name, args)

    # Handle exit command
    if result == "EXIT":
        logger.info("Exit command received.")
        console.print("Goodbye! 👋")
        sys.exit(0)


def show_help():
    """Show available commands."""
    # Use the help command from commands.py
    from djin.cli.commands import help_command

    help_command([])


def show_status():
    """Show current status (current task, timer, etc.)."""
    # This is a placeholder - will be implemented properly later
    # TODO: Integrate with state management
    console.print("[dim]Status: No active task. Timer stopped.[/dim]")


def register_all_commands():
    """Registers all core and feature commands."""
    logger.info("Registering all commands...")
    # Register core commands (example)
    register_command("help", help_command, "Show this help message")
    register_command("?", help_command, "Alias for help")
    register_command("exit", exit_command, "Exit Djin")
    register_command("quit", exit_command, "Alias for exit")

    # Register feature commands
    register_note_commands()
    register_task_commands()
    register_textsynth_commands()
    register_orchestrator_commands()
    register_accounting_commands() # Added call

    logger.info("All commands registered.")


def initialize_features():
    """Initialize features like databases."""
    logger.info("Initializing features...")
    try:
        init_notes_db()
        logger.info("Notes database initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize notes database: {str(e)}", exc_info=True)
        console.print(f"[bold red]Error initializing notes database: {e}[/bold red]")
        # Decide if you want to exit or continue without notes DB
        # sys.exit(1)
    # Call other initializers here
    logger.info("Features initialized.")


def main_loop():
    """Main application loop."""
    # Create history file directory if it doesn't exist
    history_dir = pathlib.Path("~/.Djin").expanduser()
    history_dir.mkdir(exist_ok=True)

    # Create prompt session with history
    session = PromptSession(history=FileHistory(str(history_dir / "history")), style=style)

    # Create prompt session with history
    session = PromptSession(history=FileHistory(str(history_dir / "history")), style=style)

    # --- Initialization ---
    # Register all commands *before* the loop starts
    register_all_commands()
    # Initialize features (like DBs) *before* the loop starts
    initialize_features()
    # --- End Initialization ---

    # Display welcome message
    display_welcome()

    # Main loop
    while True:
        try:
            # Show status line
            show_status()

            # Get user input
            text = session.prompt("Djin> ", style=style)

            # Skip empty input
            if not text.strip():
                continue

            # Process input
            if text.startswith("/"):
                # Handle command
                process_command(text)
            else:
                # Handle plain text (add as note)
                console.print("[cyan]Adding note:[/cyan]", text)  # Give feedback
                # Pass the text as a list of arguments to the command function
                add_note_command([text])

        except KeyboardInterrupt:
            # Handle Ctrl+C
            console.print("\n[yellow]Operation cancelled. Press Ctrl+D or type /exit to quit.[/yellow]")
            continue
        except EOFError:
            # Handle Ctrl+D to exit
            console.print("\nGoodbye! 👋")
            break
        except Exception as e:
            # Handle unexpected errors
            logger.error("An unexpected error occurred in the main loop.", exc_info=True)
            console.print(f"\n[bold red]An unexpected error occurred: {str(e)}[/bold red]")
            console.print("[yellow]Check the log file for details.[/yellow]")


if __name__ == "__main__":
    # Basic logging setup if run directly (usually configured elsewhere)
    logging.basicConfig(level=logging.INFO)
    main_loop()
