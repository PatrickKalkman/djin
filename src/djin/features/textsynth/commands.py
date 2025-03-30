"""
Command handlers for report generation and text synthesis.
"""

import logging

from rich.console import Console
from rich.panel import Panel

from djin.cli.commands import register_command
from djin.features.textsynth.agent import TextSynthAgent

# Set up logging
logger = logging.getLogger("djin.textsynth.commands")

# Create console for rich output
console = Console()
# Create text synthesis agent
textsynth_agent = TextSynthAgent()

# Log that commands are being registered
logger.info("Registering textsynth commands")


def summarize_titles_command(args):
    """Summarize multiple Jira issue titles."""
    try:
        # Check if titles were provided
        if not args:
            console.print("[red]Error: No titles provided. Usage: /summarize 'Title 1' 'Title 2' ...[/red]")
            return False

        # Get titles from arguments
        titles = args

        # Generate summary
        summary = textsynth_agent.summarize_titles(titles)

        # Display summary
        console.print(Panel(summary, title="Title Summary", border_style="green"))

        return True
    except Exception as e:
        console.print(f"[red]Error summarizing titles: {str(e)}[/red]")
        return False


def register_textsynth_commands():
    """Registers all commands related to the textsynth feature."""
    commands_to_register = {
        "summarize": (
            summarize_titles_command,
            "Summarize multiple Jira issue titles. Usage: /summarize 'Title 1' 'Title 2' ...",
        ),
        # Removed report commands: "report daily", "report weekly", "report custom"
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Textsynth commands registered: {list(commands_to_register.keys())}")
