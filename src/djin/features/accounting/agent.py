"""
Accounting agent for Djin.

Handles interactions related to accounting tasks, like registering hours.
"""

from typing import Any, Dict

from loguru import logger  # Import Loguru logger

from djin.features.accounting.graph.workflow import create_register_hours_graph

# Loguru logger is imported directly


class AccountingAgent:
    """Agent specialized in accounting operations."""

    def __init__(self):
        """Initialize the accounting agent."""
        self.register_hours_workflow = create_register_hours_graph()
        logger.info("AccountingAgent initialized with register hours workflow.")

    def _invoke_workflow(self, workflow, initial_state: Dict) -> Dict[str, Any]:
        """Helper to invoke a workflow and handle potential errors."""
        try:
            logger.debug(f"Invoking workflow with initial state: {initial_state}")
            final_state = workflow.invoke(initial_state)
            logger.debug(f"Workflow finished with final state: {final_state}")
            # Ensure essential keys exist in the final state
            return {
                "formatted_output": final_state.get("formatted_output", ""),
                "errors": final_state.get("errors", []),
                "registration_successful": final_state.get("registration_successful", False),
            }
        except Exception as e:
            logger.error(f"Workflow invocation failed: {e}", exc_info=True)
            return {
                "formatted_output": f"[red]Workflow execution failed: {str(e)}[/red]",
                "errors": [f"Workflow execution failed: {str(e)}"],
                "registration_successful": False,
            }

    def process_register_hours_request(self, date: str, description: str, hours: str) -> Dict[str, Any]:
        """
        Process a request to register hours.

        Args:
            date: Date string (YYYY-MM-DD).
            description: Description of the work.
            hours: Hours worked (as a string, will be validated in workflow).

        Returns:
            Dict containing formatted output, errors, and success status.
        """
        logger.info(f"Processing register hours request for date: {date}, hours: {hours}")
        initial_state = {
            "request_type": "register_hours",
            "date": date,
            "description": description,
            "hours": hours,  # Pass as string for validation node
            "validation_errors": [],
            "registration_successful": False,
            "registration_message": "",
            "errors": [],
            "formatted_output": "",
        }
        result = self._invoke_workflow(self.register_hours_workflow, initial_state)
        return result


# Potential future API integration
# from djin.features.accounting.api import get_accounting_api
# accounting_api = get_accounting_api()
# result = accounting_api.register_hours(date, description, hours)
