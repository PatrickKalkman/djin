"""
Prompts for report generation and text synthesis.

This module provides prompts for interacting with LLMs for report-related operations
and text synthesis.
"""

# Prompt for summarizing multiple Jira issue titles
SUMMARIZE_TITLES_PROMPT = """
You are an assistant that summarizes multiple Jira issue titles into a concise, action-oriented summary.
Given the following Jira issue titles, create a brief summary that describes what was worked on,
as if you're reporting on completed or ongoing work.

Jira Issue Titles:
{titles}

Your summary should:
1. Begin with phrases like "Worked on" or "Made progress on"
2. Be concise (1 sentence only)
3. Describe the work in an action-oriented way
4. Focus only on what was done, not on the impact or benefits
5. Be written in a clear, professional, first-person style
6. Use past tense as if reporting on work that was done
7. Do NOT include commentary about improvements, benefits, or the quality of the work
8. IMPORTANT: If the titles contain ticket IDs (like SB-1234), include ALL ticket IDs in parentheses in your summary

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
