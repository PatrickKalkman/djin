"""
Djin - A magical terminal assistant for developers.
"""

import argparse
import sys
import pathlib # Added for log path

from loguru import logger # Import Loguru logger
from rich.console import Console

from djin.cli.app import main_loop
from djin.common.config import is_configured, setup_config
from djin.common.errors import LOG_DIR, LOG_FILE, handle_error # Import log path constants

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

    # Remove default stderr sink
    logger.remove()

    # Add console sink with level INFO
    # Use Rich for console logging if desired, or Loguru's default coloring
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Add file sink with level DEBUG, rotation, and compression
    logger.add(
        LOG_FILE,
        level="DEBUG",
        rotation="10 MB",  # Rotate when file reaches 10 MB
        retention="1 week",  # Keep logs for 1 week
        compression="zip",  # Compress rotated files
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        # Use enqueue=True for async logging if needed, especially in threaded/multi-process apps
        # enqueue=True,
    )
    logger.info("Logging configured. Console level: INFO, File level: DEBUG")


def main():
    """Main entry point for Djin."""
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
