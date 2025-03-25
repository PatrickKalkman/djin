"""
Djinn - A magical terminal assistant for developers.
"""

import argparse
import sys

# Import Djinn modules
from djinn.cli.app import main_loop
from djinn.common.config import is_configured, setup_config
from djinn.common.errors import handle_error
from djinn.db.schema import backup_database, init_database, reset_database
from rich.console import Console

# Create console for rich output
console = Console()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Djinn - A magical terminal assistant for developers",
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
    """Main entry point for Djinn."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Handle setup command
        if args.setup:
            setup_config()
            init_database()
            console.print("[green]Setup complete! You can now run Djinn.[/green]")
            return 0

        # Handle reset database command
        if args.reset_db:
            confirm = input("WARNING: This will delete all your data. Are you sure? (y/N): ")
            if confirm.lower() == "y":
                backup_path = backup_database()
                if backup_path:
                    console.print(f"[yellow]Database backed up to: {backup_path}[/yellow]")

                reset_database()
                console.print("[green]Database reset complete.[/green]")
            else:
                console.print("[yellow]Database reset cancelled.[/yellow]")
            return 0

        # Handle backup database command
        if args.backup_db:
            backup_path = backup_database()
            if backup_path:
                console.print(f"[green]Database backed up to: {backup_path}[/green]")
            else:
                console.print("[yellow]No database to backup.[/yellow]")
            return 0

        # Ensure database is initialized
        init_database()

        # Check if configured
        if not is_configured():
            console.print("[yellow]Djinn is not configured yet. Running setup...[/yellow]")
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
