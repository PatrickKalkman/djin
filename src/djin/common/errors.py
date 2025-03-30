"""
Custom exceptions and error handling for Djin.
"""

import pathlib
import sys
import time
import traceback # Keep for formatting exceptions if needed, though Loguru handles it well

from loguru import logger # Import Loguru's logger
from rich.console import Console
from rich.panel import Panel

# Loguru is configured in main.py now
# Create console for rich output
console = Console()

# Define log directory (can be used by Loguru config)
LOG_DIR = pathlib.Path("~/.Djin").expanduser()
LOG_FILE = LOG_DIR / "djin.log"


class DjinError(Exception):
    """Base class for all Djin exceptions."""

    pass


class ConfigurationError(DjinError):
    """Error related to configuration."""

    pass


class DatabaseError(DjinError):
    """Error related to database operations."""

    pass


class JiraError(DjinError):
    """Error related to Jira operations."""

    pass


class TimeTrackingError(DjinError):
    """Error related to time tracking."""

    pass


class MoneyMonkError(DjinError):
    """Error related to MoneyMonk operations."""

    pass


def log_error(error, level="ERROR"):
    """Log an error using Loguru."""
    # Loguru uses string levels like "ERROR", "WARNING", "INFO", "DEBUG"
    if isinstance(error, Exception):
        # logger.exception automatically includes traceback info
        logger.opt(exception=error).log(level, str(error))
    else:
        # Log non-exception errors without traceback
        logger.log(level, str(error))


def display_error(error, title="Error"):
    """Display an error to the user."""
    if isinstance(error, DjinError):
        # Use the class name as the error type
        error_type = error.__class__.__name__
        error_message = str(error)
    else:
        # Use the exception class name
        error_type = error.__class__.__name__
        error_message = str(error)

    # Create a panel with the error information
    panel = Panel(
        f"{error_message}",
        title=f"[bold red]{title}[/bold red]",
        subtitle=f"[red]{error_type}[/red]",
        border_style="red",
    )

    console.print(panel)


def handle_error(error, exit_on_error=False):
    """Handle an error by logging and displaying it."""
    log_error(error)
    display_error(error)

    if exit_on_error:
        sys.exit(1)


def retry_operation(operation, max_retries=3, retry_delay=1, error_types=(Exception,)):
    """Retry an operation with exponential backoff."""
    retries = 0
    while retries < max_retries:
        try:
            return operation()
        except error_types as e:
            retries += 1
            if retries >= max_retries:
                raise

            delay = retry_delay * (2 ** (retries - 1))
            log_error(e, level=logging.WARNING)
            console.print(f"[yellow]Operation failed, retrying in {delay} seconds...[/yellow]")
            time.sleep(delay)
