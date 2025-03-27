"""
Task agent for Djin.

This module provides an agent specialized in task operations.
"""

from typing import Any, Dict, List

from djin.common.errors import JiraError
from djin.features.tasks.graph.workflow import create_task_fetching_graph
from djin.features.tasks.jira_client import get_issue_details, get_my_completed_issues, get_my_issues


class TaskAgent:
    """Agent specialized in task operations."""

    def __init__(self):
        """Initialize the task agent."""
        # Initialize the LangGraph workflow
        self.task_workflow = create_task_fetching_graph()

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

    def process_todo_request(self) -> str:
        """
        Process a request to show todo tasks using the LangGraph workflow.

        Returns:
            str: Formatted output of todo tasks
        """
        # Create initial state for the workflow
        initial_state = {
            "request_type": "todo",
            "raw_tasks": [],
            "processed_tasks": [],
            "formatted_output": "",
            "errors": [],
        }

        # Execute the workflow
        try:
            final_state = self.task_workflow.invoke(initial_state)
            return final_state["formatted_output"]
        except Exception as e:
            # Fallback in case the workflow fails
            try:
                # Get only issues that are in To Do status
                status_filter = "status = 'To Do'"
                issues = get_my_issues(status_filter=status_filter)

                # Convert Jira issues to dictionaries
                tasks = [self._issue_to_dict(issue) for issue in issues]

                # Format tasks for display
                from rich.console import Console

                from djin.features.tasks.display import format_tasks_table

                table = format_tasks_table(tasks, title="My To Do Tasks (Fallback)")
                console = Console(record=True)
                console.print(table)

                return console.export_text()
            except Exception as fallback_error:
                return f"Error showing To Do issues: {str(e)}\nFallback error: {str(fallback_error)}"

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
