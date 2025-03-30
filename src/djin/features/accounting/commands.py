"""
Command handlers for accounting features.
"""
import logging
from typing import List

from rich.console import Console

from djin.cli.commands import register_command
from djin.common.errors import DjinError, handle_error
# Import the API to interact with the agent/workflow
from djin.features.accounting.api import get_accounting_api

# Create console for rich output
console = Console()
logger = logging.getLogger("djin.accounting.commands")


# --- Command Handlers ---

def register_hours_command(args: List[str]) -> bool:
    """Register hours on an external platform (e.g., MoneyMonk)."""
    logger.debug(f"Received register-hours command with args: {args}")

    # Expecting: date (YYYY-MM-DD), hours (e.g., 7.5), description (multi-word)
    if len(args) < 3:
        console.print(
            "[red]Error: Missing arguments.[/red]\n"
            "Usage: /accounting register-hours <YYYY-MM-DD> <hours> <description>"
        )
        return False

    date_str = args[0]
    hours_str = args[1]
    description = " ".join(args[2:])

    console.print(f"[cyan]Attempting to register {hours_str} hours for {date_str} with description: '{description}'...[/cyan]")

    try:
        accounting_api = get_accounting_api()
        result = accounting_api.register_hours(date_str, description, hours_str)

        # Print the formatted output from the workflow/agent
        console.print(result.get("formatted_output", "[yellow]No output received from registration process.[/yellow]"))

        # Return True if the workflow reported success, False otherwise
        return result.get("registration_successful", False)

    except DjinError as e:
        # Handle known Djin errors (e.g., configuration, API connection issues if applicable)
        handle_error(e)
        return False
    except Exception as e:
        # Handle unexpected errors during the command execution
        logger.error(f"Unexpected error in register_hours_command: {e}", exc_info=True)
        handle_error(DjinError(f"An unexpected error occurred: {str(e)}"))
        return False


# --- Registration Function ---

def register_accounting_commands():
    """Registers all commands related to the accounting feature."""
    commands_to_register = {
        "accounting register-hours": (
            register_hours_command,
            "Register hours on external platform (Usage: /accounting register-hours YYYY-MM-DD hours description)",
        ),
        # Add other accounting commands here
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Accounting commands registered: {list(commands_to_register.keys())}")

# No module-level side effects for registration
