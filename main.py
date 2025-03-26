#!/usr/bin/env python3
"""
Djin: Your Terminal-Based Developer Assistant
Entry point for the application
"""

from djin.cli.app import main_loop


def main():
    """Main entry point for the application."""
    # Import all feature modules to ensure commands are registered
    import djin.features.tasks
    import djin.features.notes
    import djin.features.time
    import djin.features.moneymonk
    
    # Start the main application loop
    main_loop()


if __name__ == "__main__":
    main()
