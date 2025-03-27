"""
Public API for the task agent.

This module provides a public interface for other agents to call the task agent.
"""

from typing import Any, Dict, List, Optional

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

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get active tasks for the current user.

        Returns:
            List[Dict[str, Any]]: List of active tasks
        """
        return self._agent.get_active_tasks()

    def get_todo_tasks(self) -> str:
        """
        Get to-do tasks for the current user.

        Returns:
            str: Formatted output of todo tasks
        """
        return self._agent.process_todo_request()

    def get_todo_tasks_data(self) -> List[Dict[str, Any]]:
        """
        Get raw to-do tasks data for the current user.

        Returns:
            List[Dict[str, Any]]: List of to-do tasks
        """
        return self._agent.get_todo_tasks()

    def get_completed_tasks(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get completed tasks for the current user.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            List[Dict[str, Any]]: List of completed tasks
        """
        return self._agent.get_completed_tasks(days=days)

    def get_task_details(self, task_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific task.

        Args:
            task_key: The task key (e.g., PROJ-1234)

        Returns:
            Dict[str, Any]: Dictionary containing task details
        """
        return self._agent.get_task_details(task_key)
