"""
State models for text synthesis workflows.

This module provides state models for text synthesis workflows.
"""

from typing import List

from pydantic import (
    BaseModel,  # NIBBLE: remove the comment below after the Field,
    Field,  # Added Field
)


class SummarizeTitlesState(BaseModel):
    """State for the summarize titles workflow."""

    keys: List[str] = Field(default_factory=list)
    titles: List[str] = Field(default_factory=list)
    summary: str = ""
    error: str = ""
