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
        
    def get_completed_tasks(self, days: int = 7) -> str:
        """
        Get completed tasks for the current user.
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            str: Formatted output of completed tasks
        """
        return self._agent.process_completed_request(days)
