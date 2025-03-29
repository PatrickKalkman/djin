"""
Main CLI application loop for Djin.
"""

import pathlib
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from djin.__version__ import __version__ as VERSION

# Create console for rich output
console = Console()

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
    args = cmd_parts[1:]

    # Use the command router from commands.py
    from djin.cli.commands import route_command

    result = route_command(cmd_name, args)

    # Handle exit command
    if result == "EXIT":
        console.print("Goodbye! 👋")
        sys.exit(0)


def add_note(text):
    """Add a note for the current task."""
    # This is a placeholder - will be implemented properly later
    console.print(f"[green]Note added: {text}[/green]")


def show_help():
    """Show available commands."""
    # Use the help command from commands.py
    from djin.cli.commands import help_command

    help_command([])


def show_status():
    """Show current status (current task, timer, etc.)."""
    # This is a placeholder - will be implemented properly later
    console.print("[dim]No active task. Timer stopped.[/dim]")


def main_loop():
    """Main application loop."""
    # Create history file directory if it doesn't exist
    history_dir = pathlib.Path("~/.Djin").expanduser()
    history_dir.mkdir(exist_ok=True)

    # Create prompt session with history
    session = PromptSession(history=FileHistory(str(history_dir / "history")), style=style)

    # Import all feature modules to ensure commands are registered
    # This is done in main.py's initialize_features function

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
                add_note(text)

        except KeyboardInterrupt:
            # Handle Ctrl+C
            console.print("\n[yellow]Operation cancelled. Press Ctrl+D to exit.[/yellow]")
            continue
        except EOFError:
            # Handle Ctrl+D to exit
            console.print("\nGoodbye! 👋")
            break
        except Exception as e:
            # Handle unexpected errors
            console.print(f"\n[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    main_loop()
