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
logging_level = os.environ.get("LOGGING_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, logging_level))
logger = logging.getLogger("djin")


def initialize_features():
    """Initialize all features."""
    # Import feature commands to register them
    try:
        # Import task commands
        
        # Import report and text synthesis commands
        from djin.features.textsynth import commands as textsynth_commands

        # Log successful initialization
        logger.info("Features initialized successfully")
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
