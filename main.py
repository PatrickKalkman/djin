#!/usr/bin/env python3
"""
Djin: Your Terminal-Based Developer Assistant
Entry point for the application
"""

import logging
import os

from dotenv import load_dotenv
from rich.console import Console

from djin.cli.app import main_loop
from djin.common.config import ensure_config_dir

# Load environment variables from .env file
load_dotenv()

# Set up console
console = Console()

# Set up logging
logging_level = os.environ.get("LOGGING_LEVEL", "DEBUG")
logging.basicConfig(
    level=getattr(logging, logging_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("djin")


def initialize_features():
    """Initialize all features."""
    # Import feature commands to register them
    try:
        # Import commands module first to ensure it's initialized
        import djin.cli.commands

        logger.info("Initialized command system")

        # Import notes commands first to ensure database is initialized
        try:
            import djin.features.notes.commands
            logger.info(f"Loaded notes commands: {list(filter(lambda x: x.startswith('note'), djin.cli.commands.commands.keys()))}")
        except Exception as e:
            logger.error(f"Error loading notes commands: {str(e)}")
            console.print(f"[red]Error loading notes commands: {str(e)}[/red]")

        # Import task commands
        try:
            import djin.features.tasks.commands
            logger.info("Loaded tasks commands")
        except Exception as e:
            logger.error(f"Error loading tasks commands: {str(e)}")

        # Import report and text synthesis commands
        try:
            import djin.features.textsynth.commands
            logger.info("Loaded textsynth commands")
        except Exception as e:
            logger.error(f"Error loading textsynth commands: {str(e)}")

        # Import orchestrator commands
        try:
            import djin.features.orchestrator.commands
            logger.info("Loaded orchestrator commands")
        except Exception as e:
            logger.error(f"Error loading orchestrator commands: {str(e)}")

        # Log successful initialization
        logger.info("Features initialized successfully")
        logger.info(f"Total registered commands: {len(djin.cli.commands.commands)}")
        
        # Print all registered commands for debugging
        all_commands = list(djin.cli.commands.commands.keys())
        logger.info(f"All registered commands: {all_commands}")
    except Exception as e:
        logger.error(f"Error initializing features: {str(e)}")
        console.print(f"[red]Error initializing features: {str(e)}[/red]")


def main():
    """Main entry point for the application."""
    # Ensure config directory exists
    ensure_config_dir()

    # Initialize features
    initialize_features()

    # Start the main application loop
    main_loop()


if __name__ == "__main__":
    main()
