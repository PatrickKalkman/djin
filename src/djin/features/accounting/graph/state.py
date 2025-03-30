"""
State definitions for accounting workflows.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class RegisterHoursState(BaseModel):
    """State for the hour registration workflow."""

    request_type: str = "register_hours"
    date: str = ""
    description: str = ""
    hours: Optional[float] = None # Allow for parsing errors initially
    # Add fields for intermediate steps if needed (e.g., validation results)
    validation_errors: List[str] = Field(default_factory=list)
    # Add fields for results from TagUI interaction
    registration_successful: bool = False
    registration_message: str = ""
    # General errors
    errors: List[str] = Field(default_factory=list)
    formatted_output: str = ""
