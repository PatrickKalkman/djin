"""
Report and text synthesis agent for Djin.

This module provides an agent specialized in report generation and text synthesis.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from djin.common.errors import DjinError
from djin.features.tasks.api import TaskAPI
from djin.features.textsynth.graph.workflow import create_title_summarization_graph
from djin.features.textsynth.llm.client import ReportLLMClient

# Set up logging
logger = logging.getLogger("djin.reports")


class ReportAgent:
    """Agent specialized in report generation and text synthesis."""

    def __init__(self):
        """Initialize the report agent with necessary APIs and clients."""
        self._task_api = TaskAPI()
        self._llm_client = ReportLLMClient()
        self._title_summarization_graph = create_title_summarization_graph()

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
            
    def summarize_titles(self, titles: List[str]) -> str:
        """
        Summarize multiple Jira issue titles.
        
        Args:
            titles: List of Jira issue titles
            
        Returns:
            str: Summarized text
            
        Raises:
            DjinError: If the summarization fails
        """
        try:
            logger.info(f"Summarizing {len(titles)} Jira issue titles")
            
            # Use the workflow graph
            result = self._title_summarization_graph.invoke({"titles": titles})
            
            # Check for errors
            if result.get("error"):
                raise DjinError(result["error"])
                
            # Return the summary
            return result.get("summary", "")
        except Exception as e:
            raise DjinError(f"Failed to summarize titles: {str(e)}")
