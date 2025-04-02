"""
Node definitions for task workflows.

This module provides node functions for LangGraph workflows.
"""

from djin.features.tasks.jira_client import get_my_completed_issues, get_my_issues


# Node for fetching tasks
def fetch_tasks_node(state):
    """Fetch tasks from Jira"""
    try:
        # Fetch based on request type
        if state.request_type == "todo":
            status_filter = "status = 'To Do'"
            raw_tasks = get_my_issues(status_filter=status_filter)
        elif state.request_type == "in_progress":
            status_filter = "status = 'In Progress'"
            raw_tasks = get_my_issues(status_filter=status_filter)
        elif state.request_type == "active":
            # Active tasks include In Progress and Waiting for customer
            status_filter = "status = 'In Progress'"  # OR status = 'Waiting for customer'"
            raw_tasks = get_my_issues(status_filter=status_filter)
        elif state.request_type == "worked_on":
            # Get tasks worked on for a specific date
            from djin.features.tasks.jira_client import get_worked_on_issues

            date_str = getattr(state, "date", None)
            raw_tasks = get_worked_on_issues(date_str)
        elif state.request_type == "completed":
            days = getattr(state, "days", 7)
            raw_tasks = get_my_completed_issues(days=days)
        elif state.request_type == "task_details":
            # For task details, we'll put the result in raw_tasks even though it's a single item
            from djin.features.tasks.jira_client import get_issue_details

            issue_key = getattr(state, "issue_key", "")
            if not issue_key:
                return {"errors": state.errors + ["No issue key provided"]}
            task_details = get_issue_details(issue_key)
            raw_tasks = [task_details]  # Wrap in list to maintain consistent structure
        elif state.request_type == "set_status":
            # For set_status, we need to transition the issue
            from djin.features.tasks.jira_client import get_issue_details, transition_issue

            issue_key = getattr(state, "issue_key", "")
            status_name = getattr(state, "status_name", "")

            if not issue_key:
                return {"errors": state.errors + ["No issue key provided"]}
            if not status_name:
                return {"errors": state.errors + ["No status name provided"]}

            # First get the current details to show in the result
            task_details = get_issue_details(issue_key)

            # Then attempt the transition
            try:
                transition_issue(issue_key, status_name)
                # Mark as successful in the task details
                task_details["transition_success"] = True
                task_details["old_status"] = task_details["status"]
                task_details["new_status"] = status_name
            except Exception as e:
                # Mark as failed in the task details
                task_details["transition_success"] = False
                task_details["transition_error"] = str(e)

            raw_tasks = [task_details]  # Wrap in list to maintain consistent structure
        elif state.request_type == "create_ticket":
            # For create_ticket, we need to create a new issue
            from djin.features.tasks.jira_client import create_issue, get_issue_details

            project_key = getattr(state, "project_key", "AION")
            summary = getattr(state, "summary", "")
            description = getattr(state, "description", "")
            issue_type = getattr(state, "issue_type", "Task")

            if not summary:
                return {"errors": state.errors + ["No summary provided"]}

            # Create the issue
            try:
                new_issue_key = create_issue(project_key, summary, description, issue_type)
                # Get the details of the newly created issue
                task_details = get_issue_details(new_issue_key)
                # Mark as successful in the task details
                task_details["creation_success"] = True
                task_details["new_issue_key"] = new_issue_key
            except Exception as e:
                # Create a minimal task details dict with error info
                task_details = {
                    "creation_success": False,
                    "creation_error": str(e),
                    "summary": summary,
                    "description": description,
                    "project_key": project_key,
                    "issue_type": issue_type,
                }

            raw_tasks = [task_details]  # Wrap in list to maintain consistent structure
        else:
            raw_tasks = get_my_issues()

        return {"raw_tasks": raw_tasks}
    except Exception as e:
        return {"errors": state.errors + [f"Error fetching tasks: {str(e)}"]}


# Node for processing tasks
def process_tasks_node(state):
    """Process the raw tasks using LLM if needed"""
    # For simple todo listing, we might not need LLM processing
    # But this node allows for more complex processing in the future
    processed_tasks = []

    # Handle task_details, set_status, and create_ticket differently since they're already dictionaries
    if (state.request_type in ["task_details", "set_status", "create_ticket"]) and state.raw_tasks:
        # The task details are already processed by get_issue_details or create_issue
        processed_tasks = state.raw_tasks
    else:
        # Process regular Jira issue objects
        for issue in state.raw_tasks:
            processed_tasks.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "type": issue.fields.issuetype.name,
                "priority": getattr(issue.fields.priority, "name", "Unknown"),
                "assignee": getattr(issue.fields.assignee, "displayName", "Unassigned")
                if hasattr(issue.fields, "assignee")
                else "Unassigned",
                "worklog_seconds": getattr(issue, "worklog_seconds", 0),
            })
    return {"processed_tasks": processed_tasks}


# Node for formatting output (now primarily prepares data, not visual output)
def format_output_node(state):
    """Finalize the state, potentially adding messages or handling errors."""
    # For task_details and set_status, we still need formatted output for direct display
    if state.request_type == "task_details":
        from rich.console import Console

        from djin.features.tasks.display import format_task_details

        console = Console(record=True)
        if state.processed_tasks:
            task_details_table = format_task_details(state.processed_tasks[0])
            console.print(task_details_table)
        else:
            console.print(f"[red]No details found for issue {state.issue_key}[/red]")
        return {
            "formatted_output": console.export_text(),
            "processed_tasks": state.processed_tasks,
            "errors": state.errors,
        }

    elif state.request_type == "set_status":
        from rich.console import Console

        console = Console(record=True)
        if state.processed_tasks:
            task = state.processed_tasks[0]
            if task.get("transition_success", False):
                console.print(
                    f"[green]Successfully transitioned {task['key']} from '{task['old_status']}' to '{task['new_status']}'[/green]"
                )
            else:
                error_msg = task.get("transition_error", "Unknown error")
                console.print(f"[red]Error transitioning {task['key']}: {error_msg}[/red]")
        else:
            # This case might indicate an error fetching the task before transitioning
            console.print(f"[red]Could not retrieve details for issue {state.issue_key} to attempt transition.[/red]")
            # Add error to state if not already present
            if not any(f"Could not retrieve details for issue {state.issue_key}" in err for err in state.errors):
                state.errors.append(f"Could not retrieve details for issue {state.issue_key} before transition.")

        return {
            "formatted_output": console.export_text(),
            "processed_tasks": state.processed_tasks,
            "errors": state.errors,
        }
    
    elif state.request_type == "create_ticket":
        from rich.console import Console
        from djin.features.tasks.display import create_jira_link

        console = Console(record=True)
        if state.processed_tasks:
            task = state.processed_tasks[0]
            if task.get("creation_success", False):
                issue_key = task.get("new_issue_key", "")
                issue_link = create_jira_link(issue_key)
                console.print(f"[green]Successfully created new ticket: {issue_key}[/green]")
                console.print(f"Summary: {task.get('summary', '')}")
                console.print(f"Link: {issue_link}")
            else:
                error_msg = task.get("creation_error", "Unknown error")
                console.print(f"[red]Error creating ticket: {error_msg}[/red]")
                console.print(f"Summary: {task.get('summary', '')}")
        else:
            # This case might indicate an error in the workflow
            console.print("[red]Failed to create ticket due to an unknown error.[/red]")
            # Add error to state if not already present
            if not any("Failed to create ticket" in err for err in state.errors):
                state.errors.append("Failed to create ticket due to an unknown error.")

        return {
            "formatted_output": console.export_text(),
            "processed_tasks": state.processed_tasks,
            "errors": state.errors,
        }

    # For list-based requests, just pass through the processed tasks and errors.
    # The command layer will handle formatting the table.
    # We can add specific messages here if needed.
    elif state.request_type == "worked_on" and not state.processed_tasks:
        # Add a specific message if no 'worked_on' tasks were found
        date_display = state.date if state.date else "today"
        message = (
            f"No tasks found that you worked on {date_display}.\n"
            "This could be because:\n"
            "  • You didn't log any work for this date in Jira\n"
            "  • You didn't transition any tasks to 'In Progress' on this date\n"
            "  • You didn't update any assigned tasks on this date\n"
            "  • You didn't resolve any tasks on this date"
        )
        # Optionally, you could fetch fallback tasks here, but it might be cleaner
        # to let the command layer decide if it wants to show a fallback.
        # For now, just return the message in the errors list or a dedicated message field.
        # Let's add it to errors for simplicity.
        state.errors.append(message)

    # Return the state, ensuring processed_tasks and errors are passed through.
    # formatted_output will be empty for list-based requests now.
    return {"processed_tasks": state.processed_tasks, "errors": state.errors, "formatted_output": ""}
