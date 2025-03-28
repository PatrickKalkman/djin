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

    def process_set_status_request(self, issue_key: str, status_name: str) -> str:
        """Process a request to set the status of a specific task

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123)
            status_name: The target status name (e.g., "In Progress")

        Returns:
            str: A message indicating success or failure.
        """
        from rich.console import Console

        from djin.common.errors import handle_error
        from djin.features.tasks.jira_client import JiraError, transition_issue

        console = Console()  # Create a console instance for potential rich output within the agent if needed

        try:
            console.print(f"Attempting to transition [cyan]{issue_key}[/cyan] to status [yellow]'{status_name}'[/yellow]...")
            success = transition_issue(issue_key, status_name)
            if success:
                return f"[green]Successfully transitioned {issue_key} to '{status_name}'[/green]"
            else:
                # This might not be reached if transition_issue raises JiraError on failure
                return f"[red]Failed to transition {issue_key}. The transition might not be available.[/red]"
        except JiraError as e:
            # Log the error using handle_error but return a user-friendly message
            handle_error(e)  # Logs the error
            return f"[red]Error transitioning {issue_key}: {str(e)}[/red]"
        except Exception as e:
            # Catch unexpected errors
            handle_error(JiraError(f"An unexpected error occurred: {str(e)}")) # Logs the error
            return f"[red]An unexpected error occurred while transitioning {issue_key}: {str(e)}[/red]"

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
