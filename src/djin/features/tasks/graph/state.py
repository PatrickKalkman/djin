"""
State definitions for task workflows.

This module provides state classes for LangGraph workflows.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class TaskState(BaseModel):
    """State for the task fetching workflow"""

    request_type: str = ""  # "todo", "in_progress", "completed", etc.
    days: int = 7  # Number of days to look back for completed tasks
    raw_tasks: List[Dict] = Field(default_factory=list)
    processed_tasks: List[Dict] = Field(default_factory=list)
    formatted_output: str = ""
    errors: List[str] = Field(default_factory=list)
