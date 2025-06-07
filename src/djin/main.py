"""
Djin - A magical terminal assistant for developers.
"""

import argparse
import sys

from loguru import logger  # Import Loguru logger
from rich.console import Console

from djin.cli.app import main_loop
from djin.common.config import is_configured, setup_config
from djin.common.errors import (
    LOG_DIR,
    LOG_FILE,  # Import log path constants
    handle_error,
)

# Create console for rich output
console = Console()


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


def configure_logging():
    """Configure Loguru sinks."""
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Remove default stderr sink (which logs to stderr)
    logger.remove()

    # --- Console Sink Removed ---
    # The logger.add(sys.stderr, ...) block has been removed.
    # Logs will now primarily go to the file sink defined below.

    # Add file sink with level DEBUG, rotation, and compression
    logger.add(
        LOG_FILE,
        level="DEBUG",
        rotation="10 MB",  # Rotate when file reaches 10 MB
        retention="1 week",  # Keep logs for 1 week
        compression="zip",  # Compress rotated files
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        colorize=True,  # Added colorize=True for file logging
        # Use enqueue=True for async logging if needed, especially in threaded/multi-process apps
        # enqueue=True,
    )
    logger.info(f"Logging configured. File logging level: DEBUG at {LOG_FILE}")


def main():
    # --- Configure Logging FIRST ---
    configure_logging()
    # -------------------------------
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
