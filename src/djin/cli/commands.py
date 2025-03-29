"""
Command routing system for Djin.
"""

import logging
import inspect
from rich.console import Console
from rich.table import Table

# Set up logging
logger = logging.getLogger("djin.cli.commands")

# Create console for rich output
console = Console()

# Command registry
commands = {}

logger.info("Initializing command registry")


def register_command(name, func, help_text):
    """Register a command with the command system."""
    commands[name] = {"func": func, "help": help_text}
    logger.info(f"Registered command: {name} -> {func.__module__}.{func.__name__}")


def route_command(cmd_name, args):
    """Route a command to its handler."""
    # Check for subcommands (e.g., "tasks completed")
    full_cmd = f"{cmd_name} {args[0]}" if args else cmd_name

    if full_cmd in commands:
        # If the full command (with first arg) is registered, use it
        return commands[full_cmd]["func"](args[1:] if args else [])
    elif cmd_name in commands:
        # Otherwise use just the first part
        return commands[cmd_name]["func"](args)
    else:
        console.print(f"[red]Unknown command: {cmd_name}[/red]")
        console.print("Type [bold]/help[/bold] for available commands.")
        return False


def show_all_commands():
    """Show all available commands."""
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    for cmd_name, cmd_info in sorted(commands.items()):
        table.add_row(f"/{cmd_name}", cmd_info["help"])

    console.print(table)


# Register built-in commands
def help_command(args):
    """Show help for commands."""
    if args:
        # Show help for a specific command
        cmd_name = args[0]
        if cmd_name in commands:
            console.print(f"[bold cyan]/{cmd_name}[/bold cyan]: {commands[cmd_name]['help']}")
            return True
        else:
            console.print(f"[red]Unknown command: {cmd_name}[/red]")
            return False
    else:
        # Show all commands
        show_all_commands()
        return True


def exit_command(args):
    """Exit the application."""
    return "EXIT"


def debug_commands(args):
    """Show all registered commands (debug)."""
    console.print(f"[bold]Registered commands:[/bold] {list(commands.keys())}")
    
    # Show detailed command information
    table = Table(title="Command Details")
    table.add_column("Command", style="cyan")
    table.add_column("Help Text")
    table.add_column("Function")
    
    for cmd_name, cmd_info in sorted(commands.items()):
        table.add_row(
            f"/{cmd_name}", 
            cmd_info["help"],
            f"{cmd_info['func'].__module__}.{cmd_info['func'].__name__}"
        )
    
    console.print(table)
    return True


# Register basic commands
register_command("help", help_command, "Show help for commands")
register_command("quit", exit_command, "Exit the application")
register_command("debug", debug_commands, "Show all registered commands (debug)")
