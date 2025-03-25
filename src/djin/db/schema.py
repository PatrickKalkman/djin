"""
SQLite database schema for Djin.
"""

import pathlib
import sqlite3

from rich.console import Console

# Create console for rich output
console = Console()

# Database file path
DB_DIR = pathlib.Path("~/.Djin").expanduser()
DB_FILE = DB_DIR / "Djin.db"

# Table schemas
SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        type TEXT NOT NULL,  -- 'note', 'blocker', 'decision', 'idea'
        content TEXT NOT NULL,
        ticket_key TEXT,
        tags TEXT  -- Comma-separated tags
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS time_entries (
        id INTEGER PRIMARY KEY,
        ticket_key TEXT NOT NULL,
        started_at TIMESTAMP NOT NULL,
        ended_at TIMESTAMP,
        duration_seconds INTEGER,
        submitted BOOLEAN DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        key TEXT PRIMARY KEY,
        summary TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL,
        assignee TEXT,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        last_synced TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


def get_connection():
    """Get a connection to the database."""
    # Ensure directory exists
    DB_DIR.mkdir(exist_ok=True)

    # Create connection
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries

    return conn


def init_database():
    """Initialize the database with the schema."""
    conn = get_connection()
    cursor = conn.cursor()

    for table_sql in SCHEMA:
        cursor.execute(table_sql)

    conn.commit()
    conn.close()

    return True


def reset_database():
    """Reset the database (drop all tables and recreate)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]

    # Drop all tables
    for table in tables:
        if table != "sqlite_sequence":  # Skip internal SQLite tables
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()

    # Recreate tables
    for table_sql in SCHEMA:
        cursor.execute(table_sql)

    conn.commit()
    conn.close()

    return True


def backup_database():
    """Create a backup of the database."""
    import datetime
    import shutil

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = DB_DIR / f"Djin_{timestamp}.db.bak"

    if DB_FILE.exists():
        shutil.copy2(DB_FILE, backup_file)
        return str(backup_file)

    return None
