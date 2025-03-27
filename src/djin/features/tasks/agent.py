# tasks/agent.py
from djin.features.tasks.graph.workflow import create_task_fetching_graph


class TasksAgent:
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
