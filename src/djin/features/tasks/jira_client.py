"""
Jira client for Djin.

This module provides functions for connecting to Jira and managing stories and tasks.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger # Import Loguru logger

from jira import JIRA
from rich.console import Console
from rich.table import Table
from rich.text import Text

from djin.common.config import load_config
from djin.common.errors import JiraError

# Set up rich console
console = Console()

# Loguru logger is imported directly

# Global Jira client instance
jira_client: Optional[JIRA] = None


def get_jira_client() -> JIRA:
    """
    Get the Jira client instance, initializing it if necessary.

    Returns:
        JIRA: The Jira client instance

    Raises:
        JiraError: If the Jira client cannot be initialized
    """
    global jira_client

    if jira_client is not None:
        return jira_client

    # Load configuration
    config = load_config()
    jira_config = config.get("jira", {})

    # Check if Jira is configured
    if not jira_config.get("url") or not jira_config.get("username") or not jira_config.get("api_token"):
        raise JiraError("Jira is not configured. Run 'djin config' to set up Jira.")

    try:
        # Initialize Jira client
        jira_client = JIRA(server=jira_config["url"], basic_auth=(jira_config["username"], jira_config["api_token"]))
        return jira_client
    except Exception as e:
        raise JiraError(f"Failed to connect to Jira: {str(e)}")


def get_my_issues(status_filter: str = None) -> List[Any]:
    """
    Get issues assigned to the current user with optional status filtering.

    Args:
        status_filter: Optional status filter string for JQL (e.g., "status = 'In Progress'")

    Returns:
        List[Any]: List of JIRA issue objects
    """
    jira = get_jira_client()

    try:
        # Base JQL for assigned issues
        if status_filter:
            jql = f"assignee = currentUser() AND {status_filter} ORDER BY priority DESC, updated DESC"
        else:
            jql = (
                "assignee = currentUser() AND status != Done AND status != Resolved "
                " ORDER BY priority DESC, updated DESC"
            )

        issues = jira.search_issues(jql)

        # Fetch worklog information for each issue
        for issue in issues:
            try:
                # Add worklog data to each issue
                issue.worklog_seconds = get_issue_worklog_time(issue.key)
            except Exception as e:
                logger.error(f"Error fetching worklog for {issue.key}: {str(e)}")
                issue.worklog_seconds = 0

        return issues
    except Exception as e:
        raise JiraError(f"Failed to get assigned issues: {str(e)}")


def get_my_completed_issues(days: int = 7) -> List[Any]:
    """
    Get issues assigned to the current user that were completed in the last specified days.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        List[Any]: List of JIRA issue objects
    """
    jira = get_jira_client()

    try:
        # Get issues that were completed (Done or Resolved) in the specified days
        one_week_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        jql = (
            "assignee = currentUser() AND (status = Done OR status = Resolved) "
            f"AND updated >= {one_week_ago} ORDER BY updated DESC"
        )
        issues = jira.search_issues(jql)

        # Fetch worklog information for each issue
        for issue in issues:
            try:
                # Add worklog data to each issue
                issue.worklog_seconds = get_issue_worklog_time(issue.key)
            except Exception as e:
                logger.error(f"Error fetching worklog for {issue.key}: {str(e)}")
                issue.worklog_seconds = 0

        return issues
    except Exception as e:
        raise JiraError(f"Failed to get completed issues: {str(e)}")


def get_issue_worklog_time(issue_key: str) -> int:
    """
    Get the total time spent on an issue in seconds.

    Args:
        issue_key: The JIRA issue key

    Returns:
        int: Total time spent in seconds
    """
    jira = get_jira_client()

    try:
        worklog = jira.worklogs(issue_key)
        total_seconds = sum(entry.timeSpentSeconds for entry in worklog)
        return total_seconds
    except Exception as e:
        logger.error(f"Error fetching worklog for {issue_key}: {str(e)}")
        return 0


def format_time_spent(seconds: int) -> str:
    """
    Format time spent in a human-readable format.

    Args:
        seconds: Time spent in seconds

    Returns:
        str: Formatted time string (e.g., "2h 30m")
    """
    if seconds == 0:
        return ""

    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"


def get_issue_details(issue_key: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific issue.

    Args:
        issue_key: The JIRA issue key

    Returns:
        Dict[str, Any]: Dictionary containing issue details

    Raises:
        JiraError: If the issue cannot be found or accessed
    """
    jira = get_jira_client()

    try:
        issue = jira.issue(issue_key)

        # Build a dictionary with issue details
        details = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "type": issue.fields.issuetype.name,
            "priority": getattr(issue.fields.priority, "name", "Unknown"),
            "assignee": getattr(issue.fields.assignee, "displayName", "Unassigned")
            if hasattr(issue.fields, "assignee")
            else "Unassigned",
            "reporter": getattr(issue.fields.reporter, "displayName", "Unknown")
            if hasattr(issue.fields, "reporter")
            else "Unknown",
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "description": issue.fields.description or "",
            "worklog_seconds": get_issue_worklog_time(issue_key),
            "worklog_formatted": format_time_spent(get_issue_worklog_time(issue_key)),
        }

        # Add due date if available
        if hasattr(issue.fields, "duedate") and issue.fields.duedate:
            details["due_date"] = issue.fields.duedate

        return details
    except Exception as e:
        raise JiraError(f"Failed to get issue details for {issue_key}: {str(e)}")


def create_jira_link(issue_key: str) -> Text:
    """
    Create a clickable hyperlink for a JIRA issue key.

    Args:
        issue_key: The JIRA issue key (e.g., PROJ-1234)

    Returns:
        Text: A Rich Text object with a hyperlink that's clickable in compatible terminals
    """
    # Get Jira URL from config
    config = load_config()
    jira_url = config.get("jira", {}).get("url", "")

    # Create browse URL
    if jira_url:
        if not jira_url.endswith("/"):
            jira_url += "/"
        browse_url = f"{jira_url}browse/{issue_key}"
    else:
        # Fallback to a generic format if URL not configured
        browse_url = f"https://jira.atlassian.net/browse/{issue_key}"

    # Create a Rich Text object with a hyperlink
    text = Text(issue_key)
    text.stylize(f"link {browse_url}")
    return text


def display_issues(issues: List[Any], title: str = "My Issues") -> None:
    """
    Display a list of issues in a rich table.

    Args:
        issues: List of JIRA issue objects
        title: Title for the table
    """
    if not issues:
        console.print(f"[yellow]No issues found for: {title}[/yellow]")
        return

    # Create table
    table = Table(title=f"{title} ({len(issues)} total)")

    # Add columns
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary")
    table.add_column("Status", style="green", no_wrap=True)
    table.add_column("Priority", no_wrap=True)
    table.add_column("Time Spent", style="yellow", no_wrap=True)

    # Add rows
    for issue in issues:
        # Format time spent
        time_spent = format_time_spent(getattr(issue, "worklog_seconds", 0))

        # Add row with clickable issue key
        table.add_row(
            create_jira_link(issue.key),
            issue.fields.summary,
            issue.fields.status.name,
            getattr(issue.fields.priority, "name", "Unknown"),
            time_spent,
        )

    # Print table
    console.print(table)


def add_comment(issue_key: str, comment_text: str) -> bool:
    """
    Add a comment to an issue.

    Args:
        issue_key: The JIRA issue key
        comment_text: The comment text

    Returns:
        bool: True if successful, False otherwise

    Raises:
        JiraError: If the comment cannot be added
    """
    jira = get_jira_client()

    try:
        issue = jira.issue(issue_key)
        jira.add_comment(issue, comment_text)
        return True
    except Exception as e:
        raise JiraError(f"Failed to add comment to {issue_key}: {str(e)}")


def transition_issue(issue_key: str, transition_name: str) -> bool:
    """
    Transition an issue to a new status.

    Args:
        issue_key: The JIRA issue key
        transition_name: The name of the transition (e.g., "In Progress")

    Returns:
        bool: True if successful, False otherwise

    Raises:
        JiraError: If the transition cannot be performed
    """
    jira = get_jira_client()

    try:
        issue = jira.issue(issue_key)

        # Find the transition ID
        transitions = jira.transitions(issue)
        transition_id = None

        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break

        if not transition_id:
            available_transitions = ", ".join([t["name"] for t in transitions])
            raise JiraError(
                (
                    f"Transition '{transition_name}' not available for {issue_key}. "
                    f"Available transitions: {available_transitions}"
                )
            )

        # Perform the transition
        jira.transition_issue(issue, transition_id)
        return True
    except Exception as e:
        raise JiraError(f"Failed to transition {issue_key} to {transition_name}: {str(e)}")


def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """
    Create a new issue.

    Args:
        project_key: The project key
        summary: The issue summary
        description: The issue description
        issue_type: The issue type (default: "Task")

    Returns:
        str: The key of the created issue

    Raises:
        JiraError: If the issue cannot be created
    """
    jira = get_jira_client()

    try:
        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }

        new_issue = jira.create_issue(fields=issue_dict)
        return new_issue.key
    except Exception as e:
        raise JiraError(f"Failed to create issue: {str(e)}")


def create_subtask(parent_key: str, summary: str, description: str) -> str:
    """
    Create a subtask for a parent issue.

    Args:
        parent_key: The parent issue key
        summary: The subtask summary
        description: The subtask description

    Returns:
        str: The key of the created subtask

    Raises:
        JiraError: If the subtask cannot be created
    """
    jira = get_jira_client()

    try:
        # Get parent issue to determine project
        parent_issue = jira.issue(parent_key)

        subtask_dict = {
            "project": {"key": parent_issue.fields.project.key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Sub-task"},
            "parent": {"key": parent_key},
        }

        new_subtask = jira.create_issue(fields=subtask_dict)
        return new_subtask.key
    except Exception as e:
        raise JiraError(f"Failed to create subtask for {parent_key}: {str(e)}")


def assign_issue(issue_key: str, assignee: Optional[str] = None) -> bool:
    """
    Assign an issue to a user or to the current user if no assignee is specified.

    Args:
        issue_key: The JIRA issue key
        assignee: The username of the assignee (None for self-assignment)

    Returns:
        bool: True if successful, False otherwise

    Raises:
        JiraError: If the issue cannot be assigned
    """
    jira = get_jira_client()

    try:
        # If no assignee specified, assign to self
        if assignee is None:
            jira.assign_issue(issue_key, None)  # None means self-assignment in JIRA API
        else:
            jira.assign_issue(issue_key, assignee)
        return True
    except Exception as e:
        raise JiraError(f"Failed to assign {issue_key}: {str(e)}")


def search_issues(jql: str) -> List[Any]:
    """
    Search for issues using JQL.

    Args:
        jql: The JQL query string

    Returns:
        List[Any]: List of JIRA issue objects

    Raises:
        JiraError: If the search fails
    """
    jira = get_jira_client()

    try:
        return jira.search_issues(jql)
    except Exception as e:
        raise JiraError(f"Failed to search issues: {str(e)}")


def get_worked_on_issues(date_str: str = None) -> List[Any]:
    """
    Get issues that were worked on by the current user on a specific date.

    Args:
        date_str: Date string in YYYY-MM-DD format (default: today)

    Returns:
        List[Any]: List of JIRA issue objects

    Raises:
        JiraError: If the search fails
    """
    from datetime import date, datetime, timedelta

    jira = get_jira_client()

    try:
        # If no date provided, use today
        if not date_str:
            target_date = date.today().strftime("%Y-%m-%d")
        else:
            # Validate date format
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                target_date = date_str
            except ValueError:
                raise JiraError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

        # Parse the target date to create date range
        parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        next_day = (parsed_date + timedelta(days=1)).strftime("%Y-%m-%d")

        # Log the search parameters
        logger.info(f"Searching for issues worked on between {target_date} and {next_day}")

        # Try multiple approaches to find worked-on issues
        all_issues = []

        # 1. First try with worklogDate (standard approach)
        jql = f"worklogDate = {target_date} AND worklogAuthor = currentUser() ORDER BY updated DESC"
        logger.info(f"Executing JQL: {jql}")
        worklog_issues = jira.search_issues(jql)
        logger.info(f"Found {len(worklog_issues)} issues with worklog entries")
        all_issues.extend([issue.key for issue in worklog_issues])

        # 2. Try with updated date (might have worked on it without logging time)
        # Use a date range to ensure we catch all updates
        jql = f"assignee = currentUser() AND updated >= '{target_date} 00:00' AND updated <= '{target_date} 23:59' ORDER BY updated DESC"
        logger.info(f"Executing JQL: {jql}")
        updated_issues = jira.search_issues(jql)
        logger.info(f"Found {len(updated_issues)} issues updated on this date")
        all_issues.extend([issue.key for issue in updated_issues if issue.key not in all_issues])

        # 3. Try with status changes (e.g., moved to In Progress)
        # Look for status changes on the target date
        jql = f"assignee = currentUser() AND status CHANGED DURING ('{target_date} 00:00', '{target_date} 23:59') ORDER BY updated DESC"
        logger.info(f"Executing JQL: {jql}")
        status_changed_issues = jira.search_issues(jql)
        logger.info(f"Found {len(status_changed_issues)} issues with status changes")
        all_issues.extend([issue.key for issue in status_changed_issues if issue.key not in all_issues])

        # 4. Include all In Progress issues as a fallback
        jql = "assignee = currentUser() AND status = 'In Progress' ORDER BY updated DESC"
        logger.info(f"Executing JQL: {jql}")
        in_progress_issues = jira.search_issues(jql)
        logger.info(f"Found {len(in_progress_issues)} issues in progress")
        all_issues.extend([issue.key for issue in in_progress_issues if issue.key not in all_issues])

        # 5. Include issues that were assigned to you on this date
        jql = f"assignee = currentUser() AND assignee CHANGED DURING ('{target_date} 00:00', '{target_date} 23:59') ORDER BY updated DESC"
        logger.info(f"Executing JQL: {jql}")
        assigned_issues = jira.search_issues(jql)
        logger.info(f"Found {len(assigned_issues)} issues assigned on this date")
        all_issues.extend([issue.key for issue in assigned_issues if issue.key not in all_issues])

        # 6. Try with comments added by the user on that day
        # Note: JQL doesn't directly support comment author and date filtering efficiently.
        # A more robust solution might involve fetching recent activity streams or iterating issues,
        # but this JQL is a common approximation, though potentially slow or incomplete on large instances.
        # It finds issues *updated* during the period where the current user *was* the last commenter.
        # This isn't perfect but is the best we can do with standard JQL.
        jql = f"issueFunction in commented('by currentUser() after \"{target_date} 00:00\" before \"{target_date} 23:59\"') ORDER BY updated DESC"
        # Alternative JQL if issueFunction is not available or too slow:
        # jql = f"comment ~ currentUser() AND updated >= '{target_date} 00:00' AND updated <= '{target_date} 23:59' ORDER BY updated DESC"
        # This alternative is less precise as it matches the username anywhere in comments.
        try:
            logger.info(f"Executing JQL for comments: {jql}")
            commented_issues = jira.search_issues(jql, maxResults=50) # Limit results to avoid performance issues
            logger.info(f"Found {len(commented_issues)} issues potentially commented on (using issueFunction)")
            all_issues.extend([issue.key for issue in commented_issues if issue.key not in all_issues])
        except Exception as e:
             # Log the error but continue, as this JQL might fail depending on Jira setup (e.g., ScriptRunner not installed)
            logger.warning(f"Could not execute JQL for commented issues: {e}. This might be due to missing JQL functions (like issueFunction). Skipping this check.")


        # If we have any issues, fetch them all at once with full details
        if all_issues:
            # Remove duplicates while preserving order
            unique_issues = []
            for key in all_issues:
                if key not in unique_issues:
                    unique_issues.append(key)

            logger.info(f"Found {len(unique_issues)} unique issues in total")

            # Fetch all issues at once if there are any
            if unique_issues:
                jql = f"key in ({','.join(unique_issues)}) AND status != 'To Do' ORDER BY updated DESC"
                logger.info(f"Fetching full details with JQL: {jql}")
                issues = jira.search_issues(jql)
                logger.info(f"Successfully fetched {len(issues)} issues with full details")
            else:
                issues = []
        else:
            logger.info("No issues found across all search methods")
            issues = []

        # Fetch worklog information for each issue
        for issue in issues:
            try:
                # Add worklog data to each issue
                issue.worklog_seconds = get_issue_worklog_time(issue.key)
            except Exception as e:
                logger.error(f"Error fetching worklog for {issue.key}: {str(e)}")
                issue.worklog_seconds = 0

        return issues
    except Exception as e:
        raise JiraError(f"Failed to get issues worked on for {date_str or 'today'}: {str(e)}")


def get_available_transitions(issue_key: str) -> List[str]:
    """
    Get available transitions for an issue.

    Args:
        issue_key: The JIRA issue key

    Returns:
        List[str]: List of available transition names

    Raises:
        JiraError: If the transitions cannot be retrieved
    """
    jira = get_jira_client()

    try:
        issue = jira.issue(issue_key)
        transitions = jira.transitions(issue)
        return [t["name"] for t in transitions]
    except Exception as e:
        raise JiraError(f"Failed to get transitions for {issue_key}: {str(e)}")


def log_work(issue_key: str, time_spent: str, comment: str = "", start_time: Optional[str] = None) -> bool:
    """
    Log work on an issue.

    Args:
        issue_key: The JIRA issue key
        time_spent: Time spent in Jira format (e.g., "1h 30m")
        comment: Optional comment for the worklog
        start_time: Optional start time in ISO format

    Returns:
        bool: True if successful, False otherwise

    Raises:
        JiraError: If the work cannot be logged
    """
    jira = get_jira_client()

    try:
        jira.add_worklog(issue_key, timeSpent=time_spent, comment=comment, started=start_time)
        return True
    except Exception as e:
        raise JiraError(f"Failed to log work on {issue_key}: {str(e)}")
