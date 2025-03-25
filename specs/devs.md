# Djin: Developer Specification

Hey there, developer! Ready to build something awesome? This doc gives you everything you need to create Djin - a magical terminal assistant that'll make tedious dev tasks disappear. Let's dive right in!

## The Vision 

Djin is your terminal buddy that handles all the stuff you hate doing:
- Managing Jira tickets without tab-switching
- Tracking time without thinking about it
- Taking notes that actually stay connected to your work
- Automating those annoying MoneyMonk entries

In a nutshell: **Djin is your magical terminal companion that banishes tedious dev tasks by managing Jira tickets, tracking time, taking context-aware notes, and automating MoneyMonk entries so you can stay in your coding flow.**

## Core Requirements

### Must-Haves
- Terminal-based UI with command prompt similar to Aider
- Jira integration (Cloud API)
- Local SQLite database for notes and time tracking
- MoneyMonk automation via browser automation
- Command-based interface with `/command` syntax
- Plain text defaults to notes for current task

### Nice-to-Haves
- Clickable links in terminal
- Auto-tagging of notes
- AI-powered summaries of your work
- Background sync with Jira

## Architecture

We're using a vertical slice architecture to keep things maintainable. Each feature is self-contained with everything it needs:

```
Djin/
├── common/           # Cross-cutting concerns
│   ├── __init__.py
│   ├── config.py     # Configuration management
│   ├── state.py      # Application state
│   └── errors.py     # Custom exceptions
├── features/         # Feature slices
│   ├── __init__.py
│   ├── tasks/        # Jira task management
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   ├── jira_client.py
│   │   ├── display.py
│   │   └── models.py
│   ├── time/         # Time tracking
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   ├── tracker.py
│   │   └── models.py
│   ├── notes/        # Note taking system
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   ├── store.py
│   │   └── models.py
│   └── moneymonk/    # MoneyMonk integration
│       ├── __init__.py
│       ├── commands.py
│       ├── browser.py
│       └── models.py
├── cli/              # Terminal UI
│   ├── __init__.py
│   ├── app.py        # Main app loop
│   ├── commands.py   # Command routing
│   └── display.py    # Output formatting
├── db/               # Database management
│   ├── __init__.py
│   └── schema.py     # SQLite schema definitions
├── main.py           # Entry point
├── pyproject.toml    # Dependencies
└── README.md         # Documentation
```

## Technical Stack

- **Python 3.9+**
- **Rich** - For beautiful terminal output
- **prompt_toolkit** - For interactive terminal input
- **Jira Python** - For Jira API integration
- **SQLite** - For local storage
- **Selenium/Playwright** - For MoneyMonk automation

## Feature Details

### 1. Terminal Interface

The CLI should:
- Use prompt_toolkit for input handling
- Use Rich for output rendering
- Support command history
- Handle slash commands and plain text input
- Process keyboard interrupts gracefully
- Show a status line with current task and timer info

Sample code for the main input loop:

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

def main_loop():
    session = PromptSession(history=FileHistory('~/.Djin_history'))
    
    while True:
        try:
            text = session.prompt('> ')
            
            if text.startswith('/'):
                # Handle command
                process_command(text)
            else:
                # Handle plain text (add as note)
                add_note(text)
                
        except KeyboardInterrupt:
            # Handle Ctrl+C
            continue
        except EOFError:
            # Handle Ctrl+D to exit
            break
```

### 2. Jira Integration

Build on the existing Jira integration code you already have, but modularize it:

- Task fetching and caching
- Status updates
- Rich table display
- Task creation and updates

Key functions:
- Connect to Jira API
- Fetch assigned tasks
- Display tasks in Rich tables
- Update task status
- Create subtasks

### 3. Notes System

Create a notes system that stores:
- Timestamp
- Note type (note, blocker, decision, idea)
- Content
- Associated Jira ticket
- Auto-generated tags

SQLite schema:
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,  -- 'note', 'blocker', 'decision', 'idea'
    content TEXT NOT NULL,
    ticket_key TEXT,
    tags TEXT  -- Comma-separated tags
);
```

Tag extraction logic:
- Extract #hashtags from content
- Identify technical terms
- Record people mentioned (@name)

### 4. Time Tracking

Track time spent on tasks:
- Start/stop/pause tracking
- Handle switching between tasks
- Store in local SQLite
- Generate daily summaries

SQLite schema:
```sql
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY,
    ticket_key TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    submitted BOOLEAN DEFAULT 0
);
```

### 5. MoneyMonk Integration

Use your existing MoneyMonk automation code, but make it more robust:
- Handle browser automation edge cases
- Retry logic for network issues
- Proper error reporting

The browser automation needs to:
1. Log in securely with credentials from config
2. Handle 2FA
3. Navigate to time entry page
4. Enter time data from daily summary
5. Submit the entry
6. Verify success

## Data Handling

### Configuration
Store sensitive config in a secure way:
- Use .env file for local dev
- Use keyring for production
- Include validation

Sample config structure:
```python
{
    "jira": {
        "url": "https://your-domain.atlassian.net",
        "username": "your-email@example.com",
        "api_token": "your-token"
    },
    "moneymonk": {
        "url": "https://moneymonk.com",
        "username": "your-username",
        "totp_secret": "your-2fa-secret"
    }
}
```

### State Management
Maintain application state:
- Current task
- Timer status
- Session history

Store state in a simple JSON file that's loaded/saved as needed.

## Error Handling Strategy

Implement a comprehensive error handling strategy:
- Graceful degradation when services are down
- Informative error messages
- Automatic retry for network issues
- Logging of all errors

For each integration:
1. **Jira errors**: Cache previous results, show offline message
2. **Database errors**: Create backup file before writes, restore on corruption
3. **MoneyMonk errors**: Store failed submissions for retry

Example error handling pattern:
```python
try:
    # Operation that might fail
    result = perform_operation()
except ApiError as e:
    # Handle API errors
    log_error(e)
    show_user_friendly_message()
    use_cached_data_if_available()
except DatabaseError as e:
    # Handle database errors
    log_error(e)
    attempt_recovery()
    if recovery_failed:
        show_critical_error_message()
```

## Testing Plan

Create a comprehensive testing plan:
1. **Unit Tests**: For core business logic
2. **Integration Tests**: For database and API integrations
3. **Mock Tests**: For external services
4. **End-to-End Tests**: For full workflow

Key test cases:
- Command parsing with various inputs
- Jira API integration with mocked responses
- Database read/write operations
- Timer accuracy
- MoneyMonk form submission (with headless browser)

Use pytest fixtures to set up test environments:
```python
@pytest.fixture
def mock_jira_client():
    # Create mock Jira client
    client = MagicMock()
    client.search_issues.return_value = [mock_issue_1, mock_issue_2]
    return client

def test_fetch_tasks(mock_jira_client):
    # Test task fetching
    tasks = fetch_tasks(mock_jira_client)
    assert len(tasks) == 2
    assert tasks[0].key == "TEST-123"
```

## Deployment

The app should be installable with pip:
```
pip install Djin-assistant
```

Include a simple setup script that:
1. Creates required directories
2. Initializes the database
3. Prompts for configuration

## Implementation Roadmap

1. **Week 1: Core Framework**
   - Set up project structure
   - Implement CLI loop
   - Create database schema

2. **Week 2: Jira Integration**
   - Port existing Jira code
   - Implement Rich table display
   - Add task commands

3. **Week 3: Notes & Time Tracking**
   - Implement notes system
   - Add time tracking
   - Create command handlers

4. **Week 4: MoneyMonk & Polish**
   - Implement MoneyMonk automation
   - Add summary generation
   - Final testing and polish

## Getting Started

1. Clone the repository
2. Create a virtual environment
3. Install dependencies with `pip install -e .`
4. Copy `.env.example` to `.env` and fill in your details
5. Run with `python -m Djin`

## Resources

- Jira API Docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
- Rich Documentation: https://rich.readthedocs.io/
- Prompt Toolkit: https://python-prompt-toolkit.readthedocs.io/

---

That's it! You've got everything you need to start building Djin. This magical assistant is going to save so much time and mental energy - I can't wait to see it come to life! 

Happy coding! ✨