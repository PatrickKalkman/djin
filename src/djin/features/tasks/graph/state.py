"""
State definitions for task workflows.

This module provides state classes for LangGraph workflows.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TaskState(BaseModel):
    """State for the task fetching workflow"""

    request_type: str = ""  # "todo", "in_progress", "completed", "task_details", "set_status", "worked_on", "create_ticket", etc.
    days: int = 7  # Number of days to look back for completed tasks
    issue_key: str = ""  # Jira issue key for task_details request
    status_name: str = ""  # Status name for set_status request
    date: Optional[str] = None  # Date string for worked_on request (YYYY-MM-DD)
    # Fields for create_ticket request
    project_key: str = ""  # Project key for create_ticket request
    summary: str = ""  # Summary for create_ticket request
    description: str = ""  # Description for create_ticket request
    issue_type: str = ""  # Issue type for create_ticket request
    raw_tasks: List[Dict] = Field(default_factory=list)
    processed_tasks: List[Dict] = Field(default_factory=list)
    formatted_output: str = ""
    errors: List[str] = Field(default_factory=list)
