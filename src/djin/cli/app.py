"""
Main CLI application loop for Djin.
"""

import logging # Added logging import
import pathlib
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from djin.__version__ import __version__ as VERSION
# Import the command router and core command registration (if you create one)
from djin.cli.commands import route_command, register_command, help_command, exit_command, debug_commands
# Import the registration functions from feature modules
from djin.features.notes.commands import register_note_commands
# Import other feature command registration functions here as you create them
# from djin.features.tasks.commands import register_task_commands
# from djin.features.textsynth.commands import register_textsynth_commands
# from djin.features.orchestrator.commands import register_orchestrator_commands

# Import database initialization if you want to do it once at startup
from djin.features.notes.db.schema import init_database as init_notes_db
# Import other initializers if needed

# Create console for rich output
console = Console()
logger = logging.getLogger("djin.cli.app") # Added logger

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


def process_command(command):
    """Process a slash command."""
    cmd_parts = command[1:].split()  # Remove the slash and split

    if not cmd_parts:
        console.print("[red]Error: Empty command[/red]")
        return

    cmd_name = cmd_parts[0].lower()
    # If command has subcommands, join them for lookup, e.g., "note add"
    full_cmd_name = " ".join(cmd_parts[:2]) if len(cmd_parts) > 1 else cmd_name
    args = cmd_parts[1:] # Pass all parts after the first as args initially

    # Use the command router from commands.py
    # The router will handle finding the correct command (simple or compound)
    result = route_command(cmd_name, args) # Keep routing simple for now

    # Handle exit command
    if result == "EXIT":
        console.print("Goodbye! 👋")
        sys.exit(0)


def add_note(text):
    """Add a note using the note command."""
    # Use the actual command processing logic
    from djin.features.notes.commands import add_note_command
    add_note_command(text.split())


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
    register_command("debug", debug_commands, "Show debug information")

    # Register feature commands
    register_note_commands()
    # register_task_commands() # Uncomment when implemented
    # register_textsynth_commands() # Uncomment when implemented
    # register_orchestrator_commands() # Uncomment when implemented

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
                console.print("[cyan]Adding note:[/cyan]", text) # Give feedback
                add_note(text)

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
