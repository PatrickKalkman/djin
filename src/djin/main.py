"""
Djin - A magical terminal assistant for developers.
"""

import argparse
import sys

from rich.console import Console

from djin.cli.app import main_loop
from djin.common.config import is_configured, setup_config
from djin.common.errors import handle_error

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
