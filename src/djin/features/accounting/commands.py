"""
Command handlers for accounting features.
"""

from typing import List

from loguru import logger  # Import Loguru logger

# Import the API to interact with the agent/workflow
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # Import the specific exception
from rich.console import Console

from djin.cli.commands import register_command
from djin.common.errors import (  # Added MoneyMonkError, ConfigurationError
    ConfigurationError,
    DjinError,
    MoneyMonkError,
    handle_error,
)
from djin.features.accounting.playwright_client import login_to_moneymonk, register_hours_on_website

console = Console()


def login_command(args: List[str]) -> bool:
    """Open browser and login to MoneyMonk."""
    logger.debug(f"Received login command with args: {args}")
    
    # --- Argument Parsing ---
    headless = "--headless" in args
    if headless:
        args = [arg for arg in args if arg != "--headless"]  # Filter out the flag
    
    # No other arguments needed for login
    if args:
        console.print("[yellow]Note: This command doesn't require any arguments. Extra arguments will be ignored.[/yellow]")
    
    # --- Execute Playwright Action ---
    console.print(f"[cyan]Opening browser and logging into MoneyMonk (headless={headless})...[/cyan]")
    console.print("[cyan]Press Ctrl+C in the terminal when you're done to close the browser.[/cyan]")
    
    try:
        success = login_to_moneymonk(headless=headless)
        
        if success:
            console.print("[green]Successfully logged into MoneyMonk.[/green]")
            return True
        else:
            console.print("[red]Login failed (function returned False).[/red]")
            return False
            
    except (ConfigurationError, MoneyMonkError, PlaywrightTimeoutError) as e:
        # Handle specific known errors from the client or Playwright
        handle_error(e)  # Displays the error nicely
        return False
    except Exception as e:
        # Handle unexpected errors during the command execution
        logger.error(f"Unexpected error in login_command: {e}", exc_info=True)
        # Wrap in DjinError for consistent handling
        handle_error(DjinError(f"An unexpected error occurred during login: {str(e)}"))
        return False


def register_hours_command(args: List[str]) -> bool:
    """Register hours on MoneyMonk via Playwright automation."""
    logger.debug(f"Received register-hours command with args: {args}")

    # --- Argument Parsing ---
    headless = "--headless" in args
    if headless:
        args = [arg for arg in args if arg != "--headless"]  # Filter out the flag

    # Expecting: date (YYYY-MM-DD), hours (e.g., 7.5), description (multi-word)
    if len(args) < 3:
        console.print(
            "[red]Error: Missing arguments.[/red]\n"
            "Usage: /accounting register-hours <YYYY-MM-DD> <hours> <description> [--headless]"
        )
        return False

    date_str = args[0]
    hours_str = args[1]
    description = " ".join(args[2:])

    # --- Input Validation ---
    try:
        from datetime import datetime

        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        console.print(f"[red]Error: Invalid date format '{date_str}'. Use YYYY-MM-DD.[/red]")
        return False

    try:
        hours_float = float(hours_str)
        if hours_float <= 0:
            raise ValueError("Hours must be positive.")
    except ValueError:
        console.print(f"[red]Error: Invalid hours value '{hours_str}'. Must be a positive number.[/red]")
        return False

    if not description:
        console.print("[red]Error: Description cannot be empty.[/red]")
        return False

    # --- Execute Playwright Action ---
    console.print(
        f"[cyan]Attempting to register {hours_float} hours for {date_str} "
        f"with description: '{description}' (headless={headless})...[/cyan]"
    )

    try:
        success = register_hours_on_website(
            date=date_str, description=description, hours=hours_float, headless=headless
        )

        if success:
            console.print("[green]Successfully registered hours on MoneyMonk.[/green]")
            return True
        else:
            # This path might not be reached if register_hours_on_website raises exceptions on failure
            console.print("[red]Hour registration failed (Playwright function returned False).[/red]")
            return False

    except (ConfigurationError, MoneyMonkError, PlaywrightTimeoutError) as e:
        # Handle specific known errors from the client or Playwright
        handle_error(e)  # Displays the error nicely
        return False
    except Exception as e:
        # Handle unexpected errors during the command execution
        logger.error(f"Unexpected error in register_hours_command: {e}", exc_info=True)
        # Wrap in DjinError for consistent handling
        handle_error(DjinError(f"An unexpected error occurred during hour registration: {str(e)}"))
        return False


# --- Registration Function ---


def register_accounting_commands():
    """Registers all commands related to the accounting feature."""
    commands_to_register = {
        "accounting login": (
            login_command,
            "Open browser and login to MoneyMonk (Usage: /accounting login [--headless]).",
        ),
        "accounting register-hours": (
            register_hours_command,
            "Register hours on MoneyMonk (Usage: /accounting register-hours YYYY-MM-DD hours description [--headless]).",
        ),
        # Add other accounting commands here
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Accounting commands registered: {list(commands_to_register.keys())}")
