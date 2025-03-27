"""
Report agent for Djin.

This module provides an agent specialized in report generation.
"""

import logging
from datetime import datetime, timedelta

from djin.common.errors import DjinError
from djin.features.reports.llm.client import ReportLLMClient
from djin.features.tasks.api import TaskAPI

# Set up logging
logger = logging.getLogger("djin.reports")


class ReportAgent:
    """Agent specialized in report generation."""

    def __init__(self):
        """Initialize the report agent with necessary APIs and clients."""
        self._task_api = TaskAPI()
        self._llm_client = ReportLLMClient()

    def generate_daily_report(self) -> str:
        """
        Generate a daily report of tasks.

        Returns:
            str: Daily report
        """
        try:
            # Get today's date
            today = datetime.now().strftime("%Y-%m-%d")

            # Get active and completed tasks for today
            active_tasks = self._task_api.get_active_tasks()
            completed_tasks = self._task_api.get_completed_tasks(days=1)

            # Generate report
            report = self._llm_client.generate_daily_report(active_tasks, completed_tasks, today)

            return report
        except Exception as e:
            raise DjinError(f"Failed to generate daily report: {str(e)}")

    def generate_weekly_report(self) -> str:
        """
        Generate a weekly report of tasks.

        Returns:
            str: Weekly report
        """
        try:
            # Get date range for the week
            today = datetime.now()
            start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            end_of_week = (today + timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d")

            # Get active and completed tasks for the week
            active_tasks = self._task_api.get_active_tasks()
            completed_tasks = self._task_api.get_completed_tasks(days=7)

            # Generate report
            report = self._llm_client.generate_weekly_report(active_tasks, completed_tasks, start_of_week, end_of_week)

            return report
        except Exception as e:
            raise DjinError(f"Failed to generate weekly report: {str(e)}")

    def generate_custom_report(self, days: int = 7) -> str:
        """
        Generate a custom report of tasks.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            str: Custom report
        """
        try:
            # Get date range
            today = datetime.now()
            start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

            # Get active and completed tasks
            active_tasks = self._task_api.get_active_tasks()
            completed_tasks = self._task_api.get_completed_tasks(days=days)

            # Generate report
            report = self._llm_client.generate_custom_report(active_tasks, completed_tasks, start_date, end_date, days)

            return report
        except Exception as e:
            raise DjinError(f"Failed to generate custom report: {str(e)}")
