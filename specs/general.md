# Djinn: Your Terminal-Based Developer Assistant

## The Big Idea

Djinn lives in your terminal and handles all those annoying non-coding tasks that eat up your day. It's designed to make your work feel lighter by taking care of the admin stuff you don't enjoy.

The key features:
- Jira task management without leaving your terminal
- Super simple note-taking tied to your tasks
- Time tracking that just happens naturally as you work
- MoneyMonk automation to eliminate manual time entry

## Architecture

We're going with a vertical slice architecture because it makes way more sense for how you'll actually use this tool. Each feature is self-contained and has everything it needs.

```
djinn/
├── common/           # Stuff you need everywhere
│   ├── config.py     # Your settings and secrets
│   └── state.py      # Tracks what you're working on
├── features/         # The actual stuff that matters to you
│   ├── tasks/        # Everything about Jira tasks
│   ├── time/         # Time tracking features 
│   ├── notes/        # Your note-taking system
│   └── moneymonk/    # MoneyMonk automation
├── cli/              # The terminal interface
│   └── app.py        # Main command loop
└── main.py           # Entry point
```

This way, when you want to tweak something, everything you need is in one place.

## The User Experience

When you fire up Djinn, you'll see your current tasks from Jira right away - similar to the Rich tables you already had in your prototype, with clickable ticket links and status highlights.

Then you just interact with commands using the `/command` syntax:

```
Djinn v0.1.0
Connected to Jira Cloud ✓
Today's tasks: 5 active, 2 completed

> /start SB-1234
🚀 Started work on SB-1234: "Implement user authentication flow"
Timer running: 0:05:32

> Discovered a bug in the token refresh logic
📝 Note added to SB-1234

> /blocker API rate limiting causing issues with batch operations
🚧 Blocker recorded for SB-1234

>
```

Any text without a slash becomes a note for your current task - super handy when you're deep in work mode and just need to jot something down.

## Core Commands

### Task Management
- `/tasks` - Show your Jira dashboard with those nice rich tables
- `/start JIRA-123` - Start working on a task (and start the timer)  
- `/switch JIRA-456` - Switch to another task
- `/done` - Mark current task as done

### Notes & Context
- `/note Message` - Add a note to current task
- `/blocker Message` - Record a blocker
- `/decision Message` - Record a decision
- `/idea Message` - Save an idea for later

### Time Tracking
- `/stop` - Pause the current timer
- `/resume` - Resume the timer
- `/summary` - Generate a daily summary of what you did

### MoneyMonk Integration
- `/submit` - Submit time to MoneyMonk with your daily summary

## Technical Details

### Jira Integration
We'll build on your existing Jira integration, keeping the nice Rich tables for displaying tasks. The core functionality will:
- Fetch your assigned tickets
- Show status changes and updates
- Allow basic task management (start work, complete tasks)
- Support creating subtasks

### Notes System
All notes will be stored locally in a SQLite database with:
- Timestamp
- Type (note, blocker, decision, idea)
- Content
- Associated Jira ticket
- Tags (auto-extracted from content)

### Time Tracking
The time tracking will be simple but smart:
- Automatically tracks when you start/stop/switch tasks
- Handles interruptions gracefully
- Groups time by task for easy reporting

### MoneyMonk Automation
We'll use your existing browser automation code to:
- Log in securely with 2FA
- Navigate to the time entry page
- Submit your daily work with the right descriptions
- Handle any errors that come up

## Implementation Plan

1. **Core CLI Interface**
   - Set up the command loop and Rich display
   - Implement the command parser

2. **Jira Integration**
   - Clean up and modularize your existing code
   - Add any missing commands

3. **Notes System**
   - Create the SQLite schema
   - Implement the note-taking commands
   - Build the retrieval and summary features

4. **Time Tracking**
   - Implement the timer functionality
   - Build reporting features

5. **MoneyMonk Integration**
   - Refine your existing browser automation
   - Connect it to the daily summaries