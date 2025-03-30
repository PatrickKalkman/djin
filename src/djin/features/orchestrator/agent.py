"""
Orchestrator agent for Djin.

This module provides an agent for coordinating between different agents.
"""

import logging
from typing import Any, Dict, Optional

from djin.common.errors import DjinError
from djin.features.tasks.api import get_tasks_api # Import getter directly
from djin.features.textsynth.api import TextSynthAPI

logger = logging.getLogger("djin.orchestrator")

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
            errors = active_tasks_data.get("errors", []) + \
                     todo_tasks_data.get("errors", []) + \
                     completed_tasks_data.get("errors", [])
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
            total_time_spent = sum(task.get("worklog_seconds", 0) for task in active_tasks + completed_tasks if isinstance(task, dict))

            return {
                "active_count": len(active_tasks),
                "todo_count": len(todo_tasks),
                "completed_count": len(completed_tasks),
                "total_time_spent": total_time_spent,
            }
        except DjinError as e:
             logger.error(f"DjinError getting task overview: {e}", exc_info=True)
             raise # Re-raise known Djin errors
        except Exception as e:
            logger.error(f"Unexpected error getting task overview: {e}", exc_info=True)
            raise DjinError(f"Failed to get task overview due to an unexpected error: {str(e)}")

    def generate_work_summary(self, date_str: Optional[str] = None) -> str:
        """
        Generates a concise summary of tasks worked on for a specific date.

        Args:
            date_str: Optional date string in YYYY-MM-DD format (defaults to today).

        Returns:
            A summary string of the work done, or an error/info message.

        Raises:
            DjinError: If summary generation fails unexpectedly.
        """
        try:
            display_date = date_str or 'today'
            logger.info(f"Generating work summary for date: {display_date}")

            # 1. Get tasks worked on using the refactored TaskAPI
            # Returns Dict: {'tasks': [...], 'errors': [...]}
            worked_on_data = self._task_api.get_worked_on_tasks(date_str)
            tasks = worked_on_data.get("tasks", [])
            errors = worked_on_data.get("errors", [])

            # Handle case where no tasks were found (potentially with specific error message)
            if not tasks:
                if errors and any("No tasks found that you worked on" in e for e in errors):
                    # Return the specific message from the agent/graph node
                    no_tasks_message = next((e for e in errors if "No tasks found that you worked on" in e),
                                            f"No tasks found that were worked on for {display_date}.")
                    logger.info(f"No worked-on tasks found for {display_date}.")
                    return no_tasks_message
                elif errors:
                    # Other errors occurred during fetching
                    logger.error(f"Errors fetching worked-on tasks for {display_date}: {errors}")
                    raise DjinError(f"Failed to fetch tasks worked on for {display_date}: {'; '.join(errors)}")
                else:
                    # No tasks and no specific error message (should be rare if node adds message)
                    logger.info(f"No worked-on tasks found for {display_date} (no specific error message).")
                    return f"No tasks found that were worked on for {display_date}."


            # 2. Extract keys and titles/summaries from the retrieved tasks
            tasks_data = [
                {"key": task.get("key"), "summary": task.get("summary", "Untitled Task")}
                for task in tasks if isinstance(task, dict) and task.get("key")
            ]
            if not tasks_data:
                 # This case should be unlikely if 'tasks' is not empty, but handle defensively
                 logger.warning(f"Found tasks for {display_date}, but could not extract keys/summaries.")
                 return f"Found tasks for {display_date}, but could not extract keys or summaries."

            logger.info(f"Found {len(tasks_data)} tasks with keys and summaries to summarize for {display_date}.")

            # 3. Summarize using TextSynthAPI, passing both keys and titles
            summary = self._textsynth_api.summarize_tasks(tasks_data) # Renamed method for clarity
            logger.info(f"Generated work summary for {display_date}: {summary}")

            return summary

        except DjinError as e:
            # Catch DjinErrors raised during task fetching or summarization
            logger.error(f"DjinError generating work summary for {display_date}: {e}", exc_info=True)
            # Re-raise to be handled by the command layer
            raise
        except Exception as e:
            # Catch unexpected errors
            logger.error(f"Unexpected error generating work summary for {display_date}: {e}", exc_info=True)
            raise DjinError(f"Failed to generate work summary due to an unexpected error: {str(e)}")
