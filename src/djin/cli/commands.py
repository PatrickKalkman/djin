"""
Command routing system for Djin.
"""

import logging

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


def route_command(cmd_name: str, args: list[str]):
    """Route a command to its handler, handling subcommands and arguments."""
    logger.debug(f"Routing command: '{cmd_name}' with args: {args}")

    # Check if the command combined with the first argument is a registered command (subcommand)
    potential_subcommand = f"{cmd_name} {args[0]}" if args else None
    logger.debug(f"Checking for potential subcommand: '{potential_subcommand}'")

    if potential_subcommand and potential_subcommand in commands:
        # It's a subcommand (e.g., "tasks todo")
        logger.info(f"Found subcommand: '{potential_subcommand}', routing with args: {args[1:]}")
        return commands[potential_subcommand]["func"](args[1:])
    elif cmd_name in commands:
        # It's a base command with potential arguments (e.g., "tasks JIR-123" or just "tasks")
        logger.info(f"Found base command: '{cmd_name}', routing with args: {args}")
        return commands[cmd_name]["func"](args)
    else:
        # Command not found
        logger.warning(f"Unknown command: '{cmd_name}'")
        console.print(f"[red]Unknown command: {cmd_name}[/red]")
        console.print("Type [bold]/help[/bold] for available commands.")
        return False


def show_all_commands():
    """Show all available commands."""
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    # Log the commands that will be displayed
    logger.debug(f"Commands to display: {list(commands.keys())}")

    # Group commands by their top-level command
    command_groups = {}

    for cmd_name, cmd_info in commands.items():
        # Split the command name to get the top-level command
        parts = cmd_name.split(" ", 1)
        top_level = parts[0]

        if top_level not in command_groups:
            command_groups[top_level] = []

        # Add the command to its group
        command_groups[top_level].append((cmd_name, cmd_info))

    # Display all commands, grouped by top-level command
    for top_level, cmds in sorted(command_groups.items()):
        # First show the top-level command
        for cmd_name, cmd_info in cmds:
            if cmd_name == top_level:
                table.add_row(f"/{cmd_name}", cmd_info["help"])
                break

        # Then show all subcommands
        for cmd_name, cmd_info in sorted(cmds):
            if cmd_name != top_level:
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
        table.add_row(f"/{cmd_name}", cmd_info["help"], f"{cmd_info['func'].__module__}.{cmd_info['func'].__name__}")

    console.print(table)
    return True


# Register basic commands
register_command("help", help_command, "Show help for commands")
register_command("quit", exit_command, "Exit the application")
register_command("debug", debug_commands, "Show all registered commands (debug)")
