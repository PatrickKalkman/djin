"""
Models for report generation.

This module provides data models for report generation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from djin.features.tasks.models import Task


@dataclass
class Report:
    """Model representing a report."""

    title: str
    content: str
    generated_at: datetime
    start_date: datetime
    end_date: datetime
    active_tasks: List[Task]
    completed_tasks: List[Task]
    total_time_spent: int
