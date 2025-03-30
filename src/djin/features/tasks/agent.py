# tasks/agent.py
"""
Task agent for Djin.

This module provides an agent specialized in task operations.
"""
from typing import Any, Dict, List, Optional # Added List, Optional, Dict, Any

from loguru import logger # Import Loguru logger

from djin.features.tasks.graph.workflow import create_task_fetching_graph

# Loguru logger is imported directly

class TaskAgent:
    def __init__(self):
        # Initialize the LangGraph workflows
        self.task_fetching_workflow = create_task_fetching_graph()

    def _invoke_workflow(self, initial_state: Dict) -> Dict[str, Any]:
        """Helper to invoke workflow and handle potential errors."""
        try:
            final_state = self.task_fetching_workflow.invoke(initial_state)
            # Ensure keys exist, defaulting to empty lists/strings
            return {
                "processed_tasks": final_state.get("processed_tasks", []),
                "formatted_output": final_state.get("formatted_output", ""),
                "errors": final_state.get("errors", [])
            }
        except Exception as e:
            logger.error(f"Workflow invocation failed for type {initial_state.get('request_type')}: {e}", exc_info=True)
            return {
                "processed_tasks": [],
                "formatted_output": "",
                "errors": [f"Workflow execution failed: {str(e)}"]
            }

    def process_todo_request(self) -> Dict[str, Any]:
        """Process a request to show todo tasks. Returns processed tasks and errors."""
        initial_state = {
            "request_type": "todo",
            "raw_tasks": [], "processed_tasks": [], "formatted_output": "", "errors": [],
        }
        result = self._invoke_workflow(initial_state)
        # Return only tasks and errors for list-based requests
        return {"tasks": result["processed_tasks"], "errors": result["errors"]}

    def process_active_request(self) -> Dict[str, Any]:
        """Process a request to show active tasks. Returns processed tasks and errors."""
        initial_state = {
            "request_type": "active",
            "raw_tasks": [], "processed_tasks": [], "formatted_output": "", "errors": [],
        }
        result = self._invoke_workflow(initial_state)
        return {"tasks": result["processed_tasks"], "errors": result["errors"]}

    def process_worked_on_request(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Process a request for worked-on tasks. Returns processed tasks and errors."""
        initial_state = {
            "request_type": "worked_on",
            "date": date_str,
            "raw_tasks": [], "processed_tasks": [], "formatted_output": "", "errors": [],
        }
        result = self._invoke_workflow(initial_state)
        return {"tasks": result["processed_tasks"], "errors": result["errors"]}

    def process_completed_request(self, days: int = 7) -> Dict[str, Any]:
        """Process a request for completed tasks. Returns processed tasks and errors."""
        initial_state = {
            "request_type": "completed",
            "days": days,
            "raw_tasks": [], "processed_tasks": [], "formatted_output": "", "errors": [],
        }
        result = self._invoke_workflow(initial_state)
        return {"tasks": result["processed_tasks"], "errors": result["errors"]}

    # --- Methods returning formatted strings (Details, Status Change) ---

    def process_set_status_request(self, issue_key: str, status_name: str) -> str:
        """Process a request to set task status. Returns formatted success/error string."""
        initial_state = {
            "request_type": "set_status",
            "issue_key": issue_key,
            "status_name": status_name,
            "raw_tasks": [], "processed_tasks": [], "formatted_output": "", "errors": [],
        }
        result = self._invoke_workflow(initial_state)
        # Return formatted output directly for this type
        if result["errors"] and not result["formatted_output"]:
             # If workflow failed before formatting, return error message
             return f"[red]Error setting status: {'; '.join(result['errors'])}[/red]"
        return result["formatted_output"]

    def process_task_details_request(self, issue_key: str) -> str:
        """Process a request for task details. Returns formatted details string."""
        initial_state = {
            "request_type": "task_details",
            "issue_key": issue_key,
            "raw_tasks": [], "processed_tasks": [], "formatted_output": "", "errors": [],
        }
        result = self._invoke_workflow(initial_state)
         # Return formatted output directly for this type
        if result["errors"] and not result["formatted_output"]:
             # If workflow failed before formatting, return error message
             return f"[red]Error getting details: {'; '.join(result['errors'])}[/red]"
        return result["formatted_output"]
