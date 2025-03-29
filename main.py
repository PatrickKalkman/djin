#!/usr/bin/env python3
"""
Djin: Your Terminal-Based Developer Assistant
Entry point for the application
"""

import logging
import os

import djin.cli.commands  # Import to ensure commands module is loaded
from dotenv import load_dotenv
from rich.console import Console

from djin.cli.app import main_loop
from djin.common.config import ensure_config_dir

# Load environment variables from .env file
load_dotenv()

# Set up console
console = Console()

# Set up logging
logging_level = os.environ.get("LOGGING_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, logging_level))
logger = logging.getLogger("djin")


def initialize_features():
    """Initialize all features."""
    # Import feature commands to register them
    try:
        # Import commands module first to ensure it's initialized
        import djin.cli.commands
        logger.info("Initialized command system")
        
        # Import task commands
        import djin.features.tasks.commands
        logger.info("Loaded tasks commands")
        
        # Import report and text synthesis commands
        import djin.features.textsynth.commands
        logger.info("Loaded textsynth commands")
        
        # Import orchestrator commands
        import djin.features.orchestrator.commands
        logger.info("Loaded orchestrator commands")
        
        # Import notes commands if available
        try:
            import djin.features.notes.commands
            logger.info("Loaded notes commands")
        except ImportError:
            logger.debug("Notes feature not available")
        
        # Log successful initialization
        logger.info("Features initialized successfully")
        logger.info(f"Registered commands: {list(djin.cli.commands.commands.keys())}")
        
        # Debug: Print all registered commands
        for cmd_name in sorted(djin.cli.commands.commands.keys()):
            logger.info(f"Command registered: /{cmd_name}")
            
        # Force a debug print of all commands
        from djin.cli.commands import debug_commands
        debug_commands([])
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
