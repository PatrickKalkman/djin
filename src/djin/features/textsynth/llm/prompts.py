"""
Prompts for report generation and text synthesis.

This module provides prompts for interacting with LLMs for report-related operations
and text synthesis.
"""

# Prompt for summarizing multiple Jira issue titles
SUMMARIZE_TITLES_PROMPT = """
You are an assistant that summarizes multiple Jira issue titles into a concise summary.
Given the following Jira issue titles, create a brief summary that captures the main themes
and purposes of these issues collectively.

Jira Issue Titles:
{titles}

Your summary should:
1. Be concise (1-3 sentences)
2. Capture the main themes across all issues
3. Highlight any common goals or purposes
4. Be written in a clear, professional style
5. Avoid technical jargon unless it's essential

Summary:
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
