"""
Models for task management.

This module provides data models for task management.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Task:
    """Model representing a task."""

    key: str
    summary: str
    status: str
    type: str
    priority: str
    assignee: str
    worklog_seconds: int
    description: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    due_date: Optional[datetime] = None


@dataclass
class TaskSummary:
    """Model representing a summary of tasks."""

    active_tasks: List[Task]
    todo_tasks: List[Task]
    completed_tasks: List[Task]
    total_time_spent: int
