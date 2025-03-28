# tasks/agent.py
"""
Task agent for Djin.

This module provides an agent specialized in task operations.
"""

from djin.features.tasks.graph.workflow import create_task_fetching_graph


class TaskAgent:
    def __init__(self):
        # Initialize the LangGraph workflows
        self.task_fetching_workflow = create_task_fetching_graph()

    def process_todo_request(self):
        """Process a request to show todo tasks"""
        # Create initial state
        initial_state = {
            "request_type": "todo",
            "raw_tasks": [],
            "processed_tasks": [],
            "formatted_output": "",
            "errors": [],
        }

        # Execute the workflow - all logic happens in graph nodes
        final_state = self.task_fetching_workflow.invoke(initial_state)

        # Return the formatted output
        return final_state["formatted_output"]

    def process_completed_request(self, days: int = 7):
        """Process a request to show completed tasks

        Args:
            days: Number of days to look back (default: 7)
        """
        # Create initial state
        initial_state = {
            "request_type": "completed",
            "days": days,
            "raw_tasks": [],
            "processed_tasks": [],
            "formatted_output": "",
            "errors": [],
        }

        # Execute the workflow - all logic happens in graph nodes
        final_state = self.task_fetching_workflow.invoke(initial_state)

        # Return the formatted output
        return final_state["formatted_output"]

    def process_task_details_request(self, issue_key: str):
        """Process a request to show details for a specific task

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123)
        """
        # Create initial state
        initial_state = {
            "request_type": "task_details",
            "issue_key": issue_key,
            "raw_tasks": [],
            "processed_tasks": [],
            "formatted_output": "",
            "errors": [],
        }

        # Execute the workflow - all logic happens in graph nodes
        final_state = self.task_fetching_workflow.invoke(initial_state)

        # Return the formatted output
        return final_state["formatted_output"]
