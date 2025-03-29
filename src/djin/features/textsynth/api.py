"""
Public API for the report agent.

This module provides a public interface for other agents to call the report agent.
"""

from djin.features.textsynth.agent import ReportAgent


class ReportAPI:
    """Public API for the report agent."""

    def __init__(self):
        """Initialize the report API with a report agent."""
        self._agent = ReportAgent()

    def generate_daily_report(self) -> str:
        """
        Generate a daily report of tasks.

        Returns:
            str: Daily report
        """
        return self._agent.generate_daily_report()

    def generate_weekly_report(self) -> str:
        """
        Generate a weekly report of tasks.

        Returns:
            str: Weekly report
        """
        return self._agent.generate_weekly_report()

    def generate_custom_report(self, days: int = 7) -> str:
        """
        Generate a custom report of tasks.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            str: Custom report
        """
        return self._agent.generate_custom_report(days=days)
