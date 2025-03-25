"""
Application state management for Djin.
"""

import json
import pathlib
import threading
from datetime import datetime

# State file path
STATE_DIR = pathlib.Path("~/.Djin").expanduser()
STATE_FILE = STATE_DIR / "state.json"

# Default state
DEFAULT_STATE = {
    "current_task": None,
    "time_tracking": {"active": False, "started_at": None, "task_key": None},
    "last_sync": {"jira": None, "moneymonk": None},
}

# State lock to prevent concurrent modifications
state_lock = threading.Lock()


def load_state():
    """Load application state from file."""
    # Ensure directory exists
    STATE_DIR.mkdir(exist_ok=True)

    # Load state file if it exists, otherwise create default
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                state = DEFAULT_STATE.copy()
    else:
        state = DEFAULT_STATE.copy()
        save_state(state)

    return state


def save_state(state):
    """Save application state to file."""
    # Ensure directory exists
    STATE_DIR.mkdir(exist_ok=True)

    # Convert datetime objects to strings
    clean_state = {}
    for key, value in state.items():
        if isinstance(value, dict):
            clean_state[key] = {}
            for k, v in value.items():
                if isinstance(v, datetime):
                    clean_state[key][k] = v.isoformat()
                else:
                    clean_state[key][k] = v
        elif isinstance(value, datetime):
            clean_state[key] = value.isoformat()
        else:
            clean_state[key] = value

    # Save to file
    with open(STATE_FILE, "w") as f:
        json.dump(clean_state, f, indent=2)


def get_state():
    """Get the current application state."""
    with state_lock:
        return load_state()


def update_state(update_func):
    """Update the application state using a function."""
    with state_lock:
        state = load_state()
        updated_state = update_func(state)
        save_state(updated_state)
        return updated_state


def set_current_task(task_key):
    """Set the current task."""

    def updater(state):
        state["current_task"] = task_key
        return state

    return update_state(updater)


def get_current_task():
    """Get the current task key."""
    state = get_state()
    return state["current_task"]


def start_timer(task_key):
    """Start the timer for a task."""

    def updater(state):
        state["time_tracking"]["active"] = True
        state["time_tracking"]["started_at"] = datetime.now().isoformat()
        state["time_tracking"]["task_key"] = task_key
        return state

    return update_state(updater)


def stop_timer():
    """Stop the current timer."""

    def updater(state):
        state["time_tracking"]["active"] = False

        # Calculate duration and store time entry
        if state["time_tracking"]["started_at"]:
            # started_at = datetime.fromisoformat(state["time_tracking"]["started_at"])
            # ended_at = datetime.now()
            # duration = (ended_at - started_at).total_seconds()
            # task_key = state["time_tracking"]["task_key"]

            # Store time entry (this will be implemented in the time tracking module)
            # store_time_entry(task_key, started_at, ended_at, duration)

            # Reset timer state
            state["time_tracking"]["started_at"] = None
            state["time_tracking"]["task_key"] = None

        return state

    return update_state(updater)


def is_timer_active():
    """Check if the timer is active."""
    state = get_state()
    return state["time_tracking"]["active"]


def get_timer_info():
    """Get information about the current timer."""
    state = get_state()

    if not state["time_tracking"]["active"]:
        return None

    started_at = datetime.fromisoformat(state["time_tracking"]["started_at"])
    duration = (datetime.now() - started_at).total_seconds()

    return {
        "task_key": state["time_tracking"]["task_key"],
        "started_at": started_at,
        "duration": duration,
    }


def update_last_sync(service, timestamp=None):
    """Update the last sync timestamp for a service."""
    if timestamp is None:
        timestamp = datetime.now()

    def updater(state):
        state["last_sync"][service] = timestamp.isoformat()
        return state

    return update_state(updater)


def get_last_sync(service):
    """Get the last sync timestamp for a service."""
    state = get_state()

    if state["last_sync"][service]:
        return datetime.fromisoformat(state["last_sync"][service])

    return None
