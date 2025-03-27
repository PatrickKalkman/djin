"""
Task agent for Djin.

This module provides an agent specialized in task operations.
"""

from typing import Any, Dict, List

from djin.common.errors import JiraError
from djin.features.tasks.jira_client import get_issue_details, get_my_completed_issues, get_my_issues


class TaskAgent:
    """Agent specialized in task operations."""

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get active tasks for the current user.

        Returns:
            List[Dict[str, Any]]: List of active tasks
        """
        try:
            # Get only issues that are active (not to do, done, or resolved)
            status_filter = "status != 'To Do' AND status != 'Done' AND status != 'Resolved'"
            issues = get_my_issues(status_filter=status_filter)

            # Convert Jira issues to dictionaries
            return [self._issue_to_dict(issue) for issue in issues]
        except Exception as e:
            raise JiraError(f"Failed to get active tasks: {str(e)}")

    def get_todo_tasks(self) -> List[Dict[str, Any]]:
        """
        Get to-do tasks for the current user.

        Returns:
            List[Dict[str, Any]]: List of to-do tasks
        """
        try:
            # Get only issues that are in To Do status
            status_filter = "status = 'To Do'"
            issues = get_my_issues(status_filter=status_filter)

            # Convert Jira issues to dictionaries
            return [self._issue_to_dict(issue) for issue in issues]
        except Exception as e:
            raise JiraError(f"Failed to get to-do tasks: {str(e)}")

    def get_completed_tasks(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get completed tasks for the current user.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            List[Dict[str, Any]]: List of completed tasks
        """
        try:
            issues = get_my_completed_issues(days=days)

            # Convert Jira issues to dictionaries
            return [self._issue_to_dict(issue) for issue in issues]
        except Exception as e:
            raise JiraError(f"Failed to get completed tasks: {str(e)}")

    def get_task_details(self, task_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific task.

        Args:
            task_key: The task key (e.g., PROJ-1234)

        Returns:
            Dict[str, Any]: Dictionary containing task details
        """
        try:
            return get_issue_details(task_key)
        except Exception as e:
            raise JiraError(f"Failed to get task details for {task_key}: {str(e)}")

    def _issue_to_dict(self, issue: Any) -> Dict[str, Any]:
        """
        Convert a Jira issue object to a dictionary.

        Args:
            issue: Jira issue object

        Returns:
            Dict[str, Any]: Dictionary representation of the issue
        """
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "type": issue.fields.issuetype.name,
            "priority": getattr(issue.fields.priority, "name", "Unknown"),
            "assignee": getattr(issue.fields.assignee, "displayName", "Unassigned")
            if hasattr(issue.fields, "assignee")
            else "Unassigned",
            "worklog_seconds": getattr(issue, "worklog_seconds", 0),
        }
