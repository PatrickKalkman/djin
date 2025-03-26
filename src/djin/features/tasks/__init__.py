"""
Jira task management features
"""

from djin.features.tasks.jira_client import (
    add_comment,
    assign_issue,
    create_issue,
    create_subtask,
    display_issues,
    get_available_transitions,
    get_issue_details,
    get_jira_client,
    get_my_completed_issues,
    get_my_issues,
    log_work,
    search_issues,
    transition_issue,
)

# Import commands to register them
import djin.features.tasks.commands
