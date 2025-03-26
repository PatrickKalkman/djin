"""
Jira task management features
"""

from djin.features.tasks.jira_client import (
    get_jira_client,
    get_my_issues,
    get_my_completed_issues,
    get_issue_details,
    display_issues,
    add_comment,
    transition_issue,
    create_issue,
    create_subtask,
    assign_issue,
    search_issues,
    get_available_transitions,
    log_work
)
