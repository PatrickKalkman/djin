"""
Public API for the orchestrator agent.

This module provides a public interface for other agents to call the orchestrator agent.
"""

from typing import Any, Dict, Optional

from djin.features.orchestrator.agent import OrchestratorAgent


class OrchestratorAPI:
    """Public API for the orchestrator agent."""

    def __init__(self):
        """Initialize the orchestrator API with an orchestrator agent."""
        self._agent = OrchestratorAgent()

    def generate_task_summary(self, days: int = 7) -> str:
        """
        Generate a summary of tasks.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            str: Summary of tasks
        """
        return self._agent.generate_task_summary(days=days)

    def get_task_overview(self) -> Dict[str, Any]:
        """
        Get an overview of tasks.

        Returns:
            Dict[str, Any]: Overview of tasks
        """
        return self._agent.get_task_overview()
        
    def register_time_with_summary(self, date_str: Optional[str] = None, hours: float = 8.0) -> Dict[str, Any]:
        """
        Generate a work summary and register hours.
        
        Args:
            date_str: Optional date string in YYYY-MM-DD format (defaults to today)
            hours: Number of hours to register (defaults to 8.0)
            
        Returns:
            Dict with summary, registration result, and success status
        """
        return self._agent.register_time_with_summary(date_str, hours)
