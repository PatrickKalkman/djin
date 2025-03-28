"""
Public API for the task agent.

This module provides a public interface for other agents to call the task agent.
"""

from djin.features.tasks.agent import TaskAgent

# Singleton instance of the tasks agent
_tasks_agent = None


def get_tasks_api():
    """Get or create the tasks API"""
    global _tasks_agent
    if _tasks_agent is None:
        _tasks_agent = TaskAPI()
    return _tasks_agent


class TaskAPI:
    """Public API for the task agent."""

    def __init__(self):
        """Initialize the task API with a task agent."""
        self._agent = TaskAgent()

    def get_todo_tasks(self) -> str:
        """
        Get to-do tasks for the current user.

        Returns:
            str: Formatted output of todo tasks
        """
        return self._agent.process_todo_request()
        
    def get_active_tasks(self) -> str:
        """
        Get all active (non-completed) tasks for the current user.

        Returns:
            str: Formatted output of active tasks
        """
        return self._agent.process_active_request()
        
    def get_worked_on_tasks(self, date_str: str = None) -> str:
        """
        Get tasks worked on for a specific date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format (default: today)
            
        Returns:
            str: Formatted output of tasks worked on
        """
        return self._agent.process_worked_on_request(date_str)
        
    def get_assigned_today_tasks(self, date_str: str = None) -> str:
        """
        Get tasks assigned to the user on a specific date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format (default: today)
            
        Returns:
            str: Formatted output of tasks assigned on the specified date
        """
        return self._agent.process_assigned_today_request(date_str)

    def get_completed_tasks(self, days: int = 7) -> str:
        """
        Get completed tasks for the current user.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            str: Formatted output of completed tasks
        """
        return self._agent.process_completed_request(days)

    def get_task_details(self, issue_key: str) -> str:
        """
        Get details for a specific task.

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123)

        Returns:
            str: Formatted output of task details
        """
        return self._agent.process_task_details_request(issue_key)

    def set_task_status(self, issue_key: str, status_name: str) -> str:
        """
        Set the status for a specific task.

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123)
            status_name: The target status name (e.g., "In Progress")

        Returns:
            str: A message indicating success or failure.
        """
        return self._agent.process_set_status_request(issue_key, status_name)
