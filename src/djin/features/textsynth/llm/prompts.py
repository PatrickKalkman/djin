"""
Prompts for report generation.

This module provides prompts for interacting with LLMs for report-related operations.
"""

# Prompt for generating a daily report
DAILY_REPORT_PROMPT = """
You are an assistant that generates daily work reports. Given the following lists of
 active and completed tasks for {date}, generate a professional daily report.

Active Tasks:
{active_tasks}

Completed Tasks:
{completed_tasks}

Your report should:
1. Summarize completed work with specific accomplishments
2. Describe ongoing work and its current status
3. Be written in a professional, first-person style suitable for a daily status report
4. Be concise but comprehensive

Daily Report:
"""

# Prompt for generating a weekly report
WEEKLY_REPORT_PROMPT = """
You are an assistant that generates weekly work reports. Given the following lists of
 active and completed tasks for the week of {start_date} to {end_date}, generate a professional weekly report.

Active Tasks:
{active_tasks}

Completed Tasks:
{completed_tasks}

Your report should:
1. Summarize completed work with specific accomplishments
2. Describe ongoing work and its current status
3. Group related tasks together
4. Highlight key achievements and milestones
5. Be written in a professional, first-person style suitable for a weekly status report
6. Be concise but comprehensive

Weekly Report:
"""

# Prompt for generating a custom report
CUSTOM_REPORT_PROMPT = """
You are an assistant that generates work reports. Given the following lists of
 active and completed tasks for the period of {start_date} to {end_date} ({days} days),
 generate a professional report.

Active Tasks:
{active_tasks}

Completed Tasks:
{completed_tasks}

Your report should:
1. Summarize completed work with specific accomplishments
2. Describe ongoing work and its current status
3. Group related tasks together
4. Highlight key achievements and milestones
5. Be written in a professional, first-person style suitable for a status report
6. Be concise but comprehensive

Report:
"""
