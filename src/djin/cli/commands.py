"""
Command routing system for Djin.
"""

from rich.console import Console
from rich.table import Table

# Create console for rich output
console = Console()

# Command registry
commands = {}


def register_command(name, func, help_text):
    """Register a command with the command system."""
    commands[name] = {"func": func, "help": help_text}


def route_command(cmd_name, args):
    """Route a command to its handler."""
    if cmd_name in commands:
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


# Register basic commands
register_command("help", help_command, "Show help for commands")
register_command("exit", exit_command, "Exit the application")
register_command("quit", exit_command, "Exit the application")
