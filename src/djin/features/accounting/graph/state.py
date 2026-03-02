"""
ABOUTME: State definitions for accounting workflows.
ABOUTME: Defines Pydantic models used by the hour registration LangGraph workflow.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class RegisterHoursState(BaseModel):
    """State for the hour registration workflow."""

    request_type: str = "register_hours"
    date: str = ""
    description: str = ""
    hours: Optional[float] = None
    project_name: str = ""
    validation_errors: List[str] = Field(default_factory=list)
    registration_successful: bool = False
    registration_message: str = ""
    errors: List[str] = Field(default_factory=list)
    formatted_output: str = ""
