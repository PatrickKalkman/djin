"""
Prompts for task operations.

This module provides prompts for interacting with LLMs for task-related operations.
"""

# Prompt for summarizing tasks
TASK_SUMMARY_PROMPT = """
You are an assistant that summarizes tasks. Given the following list of tasks, 
provide a concise summary of the work that has been done and the work that is in progress.

Tasks:
{tasks}

Your summary should:
1. Group related tasks together
2. Highlight key accomplishments
3. Identify ongoing work
4. Be professional and concise

Summary:
"""

# Prompt for generating a task report
TASK_REPORT_PROMPT = """
You are an assistant that generates reports on work activities. Given the following lists of 
active and completed tasks, generate a professional report summarizing the work.

Active Tasks:
{active_tasks}

Completed Tasks:
{completed_tasks}

Your report should:
1. Summarize completed work with specific accomplishments
2. Describe ongoing work and its current status
3. Group related tasks together
4. Be written in a professional, first-person style suitable for a status report
5. Be concise but comprehensive

Report:
"""

# Prompt for analyzing task patterns
TASK_PATTERN_PROMPT = """
You are an assistant that analyzes work patterns. Given the following history of tasks,
identify patterns, bottlenecks, and suggestions for improvement.

Task History:
{task_history}

Your analysis should include:
1. Patterns in task completion (e.g., types of tasks that take longer)
2. Potential bottlenecks in the workflow
3. Suggestions for improving productivity
4. Any notable trends

Analysis:
"""
