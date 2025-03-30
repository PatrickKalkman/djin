"""
Commands for the notes feature.
"""

import logging
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import register_command from the central location
from djin.cli.commands import register_command
from djin.features.notes.db.schema import get_connection, init_database

# Set up logging
logger = logging.getLogger("djin.notes.commands")

# Create console for rich output
console = Console()


def add_note_command(args: List[str]) -> bool:
    """Add a new note."""
    if not args:
        console.print("[red]Error: Note text is required[/red]")
        console.print("Usage: /note add <text>")
        return False

    note_text = " ".join(args)

    try:
        # Ensure DB is initialized before first use in a command
        # Consider moving init_database() to app startup if preferred
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (type, content) VALUES (?, ?)",
            ("note", note_text)
        )
        conn.commit()
        note_id = cursor.lastrowid
        logger.info(f"Added note with ID {note_id}")
        console.print(f"[green]Note added successfully (ID: {note_id})[/green]")
        return True
    except Exception as e:
        logger.error(f"Error adding note: {str(e)}")
        console.print(f"[red]Error adding note: {str(e)}[/red]")
        return False


def list_notes_command(args: List[str]) -> bool:
    """List all notes."""
    try:
        # Ensure DB is initialized before first use in a command
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, created_at, type, content FROM notes ORDER BY created_at DESC LIMIT 20"
        )
        notes = cursor.fetchall()
        
        if not notes:
            console.print("[yellow]No notes found[/yellow]")
            return True
            
        table = Table(title="Notes")
        table.add_column("ID", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Type", style="magenta")
        table.add_column("Content")
        
        for note in notes:
            table.add_row(
                str(note[0]),
                note[1],
                note[2],
                note[3][:100] + ("..." if len(note[3]) > 100 else "")
            )
            
        console.print(table)
        return True
    except Exception as e:
        logger.error(f"Error listing notes: {str(e)}")
        console.print(f"[red]Error listing notes: {str(e)}[/red]")
        return False


def view_note_command(args: List[str]) -> bool:
    """View a specific note by ID."""
    if not args:
        console.print("[red]Error: Note ID is required[/red]")
        console.print("Usage: /note view <id>")
        return False
        
    try:
        note_id = int(args[0])
    except ValueError:
        console.print("[red]Error: Note ID must be a number[/red]")
        return False
        
    try:
        # Ensure DB is initialized before first use in a command
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, created_at, type, content FROM notes WHERE id = ?",
            (note_id,)
        )
        note = cursor.fetchone()
        
        if not note:
            console.print(f"[yellow]Note with ID {note_id} not found[/yellow]")
            return False
            
        console.print(Panel(
            note[3],
            title=f"Note #{note[0]} ({note[1]})",
            subtitle=f"Type: {note[2]}",
            border_style="green"
        ))
        return True
    except Exception as e:
        logger.error(f"Error viewing note: {str(e)}")
        console.print(f"[red]Error viewing note: {str(e)}[/red]")
        return False


def debug_notes_db_command(args: List[str]) -> bool:
    """Debug the notes database."""
    try:
        # Ensure DB is initialized before first use in a command
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        # Check if the notes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
        tables = cursor.fetchall()
        if not tables:
            console.print("[red]Notes table does not exist![/red]")
            # init_database() was already called, maybe log differently
            console.print("[yellow]Database should have been initialized. Check for errors.[/yellow]")
        else:
            console.print("[green]Notes table exists[/green]")
        # Get table schema
        cursor.execute("PRAGMA table_info(notes)")
        schema = cursor.fetchall()
        
        table = Table(title="Notes Table Schema")
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("NotNull", style="magenta")
        table.add_column("Default", style="yellow")
        
        for col in schema:
            table.add_row(
                col[1],  # name
                col[2],  # type
                str(col[3]),  # notnull
                str(col[4])   # default
            )
            
        console.print(table)
        return True
    except Exception as e:
        logger.error(f"Error debugging notes database: {str(e)}")
        console.print(f"[red]Error debugging notes database: {str(e)}[/red]")
        return False


def delete_note_command(args: List[str]) -> bool:
    """Delete a note by ID."""
    if not args:
        console.print("[red]Error: Note ID is required[/red]")
        console.print("Usage: /note delete <id>")
        return False
        
    try:
        note_id = int(args[0])
    except ValueError:
        console.print("[red]Error: Note ID must be a number[/red]")
        return False
        
    try:
        # Ensure DB is initialized before first use in a command
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM notes WHERE id = ?", (note_id,))
        if not cursor.fetchone():
            console.print(f"[yellow]Note with ID {note_id} not found[/yellow]")
            return False
            
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        logger.info(f"Deleted note with ID {note_id}")
        console.print(f"[green]Note {note_id} deleted successfully[/green]")
        return True
    except Exception as e:
        logger.error(f"Error deleting note: {str(e)}")
        console.print(f"[red]Error deleting note: {str(e)}[/red]")
        return False


def note_command(args: List[str]) -> bool:
    """Main note command handler."""
    if not args:
        # Default to listing notes if no subcommand
        return list_notes_command([])
        
    subcommand = args[0].lower()
    if subcommand == "add":
        return add_note_command(args[1:])
    elif subcommand == "list":
        return list_notes_command(args[1:])
    elif subcommand == "view":
        return view_note_command(args[1:])
    elif subcommand == "delete":
        return delete_note_command(args[1:])
    else:
        console.print(f"[red]Unknown note subcommand: {subcommand}[/red]")
        console.print("Available subcommands: add, list, view, delete")
        return False

# --- Registration Function ---

def register_note_commands():
    """Registers all commands related to the notes feature."""
    commands_to_register = {
        "note": (note_command, "Manage notes (add, list, view, delete)"),
        "note add": (add_note_command, "Add a new note"),
        "note list": (list_notes_command, "List all notes"),
        "note view": (view_note_command, "View a specific note by ID"),
        "note delete": (delete_note_command, "Delete a note by ID"),
        "note debug": (debug_notes_db_command, "Debug the notes database"),
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Notes commands registered: {list(commands_to_register.keys())}")

# --- Remove Module-Level Side Effects ---
# Remove the old module-level registration calls
# Remove the module-level init_database() call
