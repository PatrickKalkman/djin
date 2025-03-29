"""
Orchestrator agent for Djin.

This module provides an agent for coordinating between different agents.
"""

import logging
from typing import Any, Dict

from djin.common.errors import DjinError
from djin.features.tasks.api import TaskAPI
from djin.features.textsynth.api import ReportAPI

# Set up logging
logger = logging.getLogger("djin.orchestrator")


class OrchestratorAgent:
    """Agent for coordinating between different agents."""

    def __init__(self):
        """Initialize the orchestrator agent with necessary APIs."""
        self._task_api = TaskAPI()
        self._report_api = ReportAPI()

    def generate_task_summary(self, days: int = 7) -> str:
        """
        Generate a summary of tasks.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            str: Summary of tasks

        Raises:
            DjinError: If the summary cannot be generated
        """
        try:
            # Use the report API to generate a custom report
            return self._report_api.generate_custom_report(days=days)
        except Exception as e:
            raise DjinError(f"Failed to generate task summary: {str(e)}")

    def get_task_overview(self) -> Dict[str, Any]:
        """
        Get an overview of tasks.

        Returns:
            Dict[str, Any]: Overview of tasks

        Raises:
            DjinError: If the overview cannot be generated
        """
        try:
            # Get active, todo, and completed tasks
            active_tasks = self._task_api.get_active_tasks()
            todo_tasks = self._task_api.get_todo_tasks()
            completed_tasks = self._task_api.get_completed_tasks(days=7)

            # Calculate total time spent
            total_time_spent = sum(task.get("worklog_seconds", 0) for task in active_tasks + completed_tasks)

            # Return overview
            return {
                "active_count": len(active_tasks),
                "todo_count": len(todo_tasks),
                "completed_count": len(completed_tasks),
                "total_time_spent": total_time_spent,
            }
        except Exception as e:
            raise DjinError(f"Failed to get task overview: {str(e)}")
