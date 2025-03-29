"""
State models for text synthesis workflows.

This module provides state models for text synthesis workflows.
"""

from typing import List

from pydantic import BaseModel


class SummarizeTitlesState(BaseModel):
    """State for the summarize titles workflow."""

    titles: List[str]
    summary: str = ""
    error: str = ""
