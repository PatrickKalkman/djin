"""
ABOUTME: Orchestrator agent for Djin.
ABOUTME: Coordinates task fetching, summarization, and hour registration across customers.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from djin.common.errors import DjinError
from djin.features.tasks.api import get_tasks_api
from djin.features.textsynth.api import TextSynthAPI

logger = logging.getLogger("djin.orchestrator")

CUSTOMERS = {
    "AION": {
        "task_source": "jira",
        "moneymonk_project": "AION Titan",
    },
    "LG": {
        "task_source": "ado",
        "moneymonk_project": "LLM Project",
        "ado_org": "hoogendoorn-growthmanagement",
        "ado_project": "DataAnalytics",
    },
}


class OrchestratorAgent:
    def __init__(self):
        """Initialize the orchestrator agent with necessary APIs."""
        # Use the API getter function to ensure singleton TaskAPI if desired
        self._task_api = get_tasks_api()
        # Assuming TextSynthAPI can be instantiated directly or has its own getter
        self._textsynth_api = TextSynthAPI()

    def get_task_overview(self) -> Dict[str, Any]:
        """
        Get an overview of tasks.

        Returns:
            Dict[str, Any]: Overview of tasks {active_count, todo_count, completed_count, total_time_spent}

        Raises:
            DjinError: If the overview cannot be generated or task fetching fails.
        """
        try:
            # Get task data using the updated API (returns Dict with 'tasks' and 'errors')
            active_tasks_data = self._task_api.get_active_tasks()
            todo_tasks_data = self._task_api.get_todo_tasks()
            completed_tasks_data = self._task_api.get_completed_tasks(days=7)

            # Check for errors from API calls
            errors = (
                active_tasks_data.get("errors", [])
                + todo_tasks_data.get("errors", [])
                + completed_tasks_data.get("errors", [])
            )
            if errors:
                # Log the errors but attempt to continue if some data was retrieved
                logger.warning(f"Errors encountered while fetching tasks for overview: {errors}")
                # Optionally raise an error if any fetch completely failed
                # if not active_tasks_data.get("tasks") and not todo_tasks_data.get("tasks") ... etc.
                # For now, we proceed with potentially partial data.

            # Extract the lists of tasks
            active_tasks = active_tasks_data.get("tasks", [])
            todo_tasks = todo_tasks_data.get("tasks", [])
            completed_tasks = completed_tasks_data.get("tasks", [])

            # Calculate total time spent - Ensure 'worklog_seconds' exists in the dicts
            total_time_spent = sum(
                task.get("worklog_seconds", 0) for task in active_tasks + completed_tasks if isinstance(task, dict)
            )

            return {
                "active_count": len(active_tasks),
                "todo_count": len(todo_tasks),
                "completed_count": len(completed_tasks),
                "total_time_spent": total_time_spent,
            }
        except DjinError as e:
            logger.error(f"DjinError getting task overview: {e}", exc_info=True)
            raise  # Re-raise known Djin errors
        except Exception as e:
            logger.error(f"Unexpected error getting task overview: {e}", exc_info=True)
            raise DjinError(f"Failed to get task overview due to an unexpected error: {str(e)}")

    def _get_tasks_for_customer(self, customer: str, date_str: Optional[str] = None) -> list:
        """
        Fetch tasks/work items for a customer from the appropriate source.

        Returns:
            List of normalized task dicts with 'key' and 'summary' fields.

        Raises:
            DjinError: If customer is unknown or fetching fails.
        """
        config = CUSTOMERS.get(customer)
        if not config:
            raise DjinError(f"Unknown customer '{customer}'. Valid customers: {', '.join(CUSTOMERS.keys())}")

        if config["task_source"] == "jira":
            worked_on_data = self._task_api.get_worked_on_tasks(date_str)
            tasks = worked_on_data.get("tasks", [])
            errors = worked_on_data.get("errors", [])

            if not tasks and errors:
                real_errors = [e for e in errors if "No tasks found that you worked on" not in e]
                if real_errors:
                    raise DjinError(f"Failed to fetch Jira tasks: {'; '.join(real_errors)}")
                return []
            return tasks

        elif config["task_source"] == "ado":
            from djin.features.tasks.ado_client import get_worked_on_items

            return get_worked_on_items(
                org=config["ado_org"],
                project=config["ado_project"],
                date_str=date_str or datetime.now().strftime("%Y-%m-%d"),
            )

        raise DjinError(f"Unknown task source '{config['task_source']}' for customer '{customer}'")

    def generate_work_summary(self, date_str: Optional[str] = None, customer: str = "AION") -> str:
        """
        Generates a concise summary of tasks worked on for a specific date and customer.

        Args:
            date_str: Optional date string in YYYY-MM-DD format (defaults to today).
            customer: Customer code (e.g. "AION", "LG").

        Returns:
            A summary string of the work done, or an error/info message.

        Raises:
            DjinError: If summary generation fails unexpectedly.
        """
        try:
            display_date = date_str or "today"
            logger.info(f"Generating work summary for {customer} on {display_date}")

            tasks = self._get_tasks_for_customer(customer, date_str)

            if not tasks:
                logger.info(f"No worked-on tasks found for {customer} on {display_date}.")
                return f"No tasks found that were worked on for {display_date}."

            tasks_data = [
                {"key": task.get("key"), "summary": task.get("summary", "Untitled Task")}
                for task in tasks
                if isinstance(task, dict) and task.get("key")
            ]
            if not tasks_data:
                logger.warning(f"Found tasks for {display_date}, but could not extract keys/summaries.")
                return f"Found tasks for {display_date}, but could not extract keys or summaries."

            logger.info(f"Found {len(tasks_data)} tasks to summarize for {customer} on {display_date}.")

            summary = self._textsynth_api.summarize_tasks(tasks_data)
            logger.info(f"Generated work summary for {customer} on {display_date}: {summary}")

            return summary

        except DjinError as e:
            logger.error(f"DjinError generating work summary for {customer} on {display_date}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating work summary for {customer} on {display_date}: {e}", exc_info=True)
            raise DjinError(f"Failed to generate work summary due to an unexpected error: {str(e)}")

    def register_time_with_summary(
        self, date_str: Optional[str] = None, hours: float = 8.0, customer: str = "AION"
    ) -> Dict[str, Any]:
        """
        Generates a work summary and registers the hours on MoneyMonk.

        Args:
            date_str: Optional date string in YYYY-MM-DD format (defaults to today).
            hours: Number of hours to register (defaults to 8.0).
            customer: Customer code (e.g. "AION", "LG").

        Returns:
            Dict with keys:
                - summary: The generated work summary
                - registration_result: Result from the accounting API
                - success: Overall success status

        Raises:
            DjinError: If the operation fails unexpectedly.
        """
        try:
            config = CUSTOMERS.get(customer)
            if not config:
                raise DjinError(f"Unknown customer '{customer}'. Valid customers: {', '.join(CUSTOMERS.keys())}")

            display_date = date_str or "today"
            logger.info(f"Registering time for {customer} on {display_date}, hours: {hours}")

            summary = self.generate_work_summary(date_str, customer=customer)

            if "No tasks found" in summary:
                return {
                    "summary": summary,
                    "registration_result": None,
                    "success": False,
                    "error": "Cannot register time: No tasks were found for this date.",
                }

            from djin.features.accounting.api import get_accounting_api

            accounting_api = get_accounting_api()

            registration_result = accounting_api.register_hours(
                date=date_str or datetime.now().strftime("%Y-%m-%d"),
                description=summary,
                hours=str(hours),
                project_name=config["moneymonk_project"],
            )

            success = registration_result.get("registration_successful", False)
            return {
                "summary": summary,
                "registration_result": registration_result,
                "success": success,
                "error": None if success else registration_result.get("errors", ["Registration failed"])[0],
            }

        except DjinError as e:
            logger.error(f"DjinError in register_time_with_summary: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in register_time_with_summary: {e}", exc_info=True)
            raise DjinError(f"Failed to register time with summary: {str(e)}")
