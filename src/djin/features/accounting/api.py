"""
Public API for the accounting agent.
"""

from typing import Any, Dict

from loguru import logger  # Import Loguru logger

from djin.features.accounting.agent import AccountingAgent

# Singleton instance
_accounting_agent_api = None


def get_accounting_api():
    """Get or create the accounting API."""
    global _accounting_agent_api
    if _accounting_agent_api is None:
        logger.info("Creating AccountingAPI singleton instance.")
        _accounting_agent_api = AccountingAPI()
    return _accounting_agent_api


class AccountingAPI:
    """Public API for the accounting agent."""

    def __init__(self):
        """Initialize the accounting API with an agent."""
        self._agent = AccountingAgent()
        logger.debug("AccountingAPI initialized with AccountingAgent.")

    def register_hours(self, date: str, description: str, hours: str) -> Dict[str, Any]:
        """
        Register hours via the accounting agent.

        Args:
            date: Date string (YYYY-MM-DD).
            description: Description of the work.
            hours: Hours worked (as string for initial processing).

        Returns:
            Dict containing formatted output, errors, and success status from the agent.
        """
        logger.info(f"AccountingAPI received register_hours request: date={date}, hours={hours}")
        return self._agent.process_register_hours_request(date, description, hours)

    # Add other accounting-related API methods here if needed
    # e.g., def get_unregistered_time(...)
