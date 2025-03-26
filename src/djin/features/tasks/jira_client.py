"""
Jira client for Djin.

This module provides functions for connecting to Jira and managing stories and tasks.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from jira import JIRA
from rich.console import Console
from rich.table import Table
from rich.text import Text

from djin.common.config import load_config
from djin.common.errors import JiraError, retry_operation

# Set up rich console
console = Console()

# Set up logging
logger = logging.getLogger("djin.jira")

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
        jira_client = JIRA(
            server=jira_config["url"],
            basic_auth=(jira_config["username"], jira_config["api_token"])
        )
        return jira_client
    except Exception as e:
        raise JiraError(f"Failed to connect to Jira: {str(e)}")


def get_my_issues() -> List[Any]:
    """
    Get issues assigned to the current user that are not done.

    Returns:
        List[Any]: List of JIRA issue objects
    """
    jira = get_jira_client()

    try:
        jql = "assignee = currentUser() AND status != Done AND status != Resolved ORDER BY priority DESC, updated DESC"
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
        jql = f"assignee = currentUser() AND (status = Done OR status = Resolved) AND updated >= {one_week_ago} ORDER BY updated DESC"
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
            "assignee": getattr(issue.fields.assignee, "displayName", "Unassigned") if hasattr(issue.fields, "assignee") else "Unassigned",
            "reporter": getattr(issue.fields.reporter, "displayName", "Unknown") if hasattr(issue.fields, "reporter") else "Unknown",
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
            time_spent
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
            raise JiraError(f"Transition '{transition_name}' not available for {issue_key}. Available transitions: {available_transitions}")
            
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
        jira.add_worklog(
            issue_key, 
            timeSpent=time_spent, 
            comment=comment,
            started=start_time
        )
        return True
    except Exception as e:
        raise JiraError(f"Failed to log work on {issue_key}: {str(e)}")
