"""
State definitions for task workflows.

This module provides state classes for LangGraph workflows.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class TaskState(BaseModel):
    """State for the task fetching workflow"""
    request_type: str = ""  # "todo", "in_progress", etc.
    raw_tasks: List[Dict] = Field(default_factory=list)
    processed_tasks: List[Dict] = Field(default_factory=list)
    formatted_output: str = ""
    errors: List[str] = Field(default_factory=list)
