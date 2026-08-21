"""
ABOUTME: Prompt templates for text synthesis operations.
ABOUTME: Contains the prompt for summarizing work items into a time entry description.
"""

# Prompt for summarizing multiple work item titles including their keys
SUMMARIZE_TITLES_PROMPT = """
You are an assistant that summarizes multiple work items into a concise, action-oriented summary.
Given the following work items (Key: Title format), create a brief summary that describes what was worked on,
as if you're reporting on completed or ongoing work.

Work Items:
{issues}

Your summary should:
1. Begin with phrases like "Worked on" or "Made progress on".
2. Be concise (1 sentence only).
3. Describe the work in an action-oriented way.
4. Focus only on what was done, not on the impact or benefits.
5. Be written in a clear, professional, first-person style.
6. Use past tense as if reporting on work that was done.
7. Do NOT include commentary about improvements, benefits, or the quality of the work.
8. IMPORTANT: Include the corresponding work item key (e.g., PROJ-123 or DA-456) in parentheses immediately after mentioning the work related to that item.

Example Input:
Work Items:
- TASK-1: Fix login bug
- FEAT-2: Implement new dashboard
- DA-42: Update data pipeline

Example Output:
Worked on fixing a login bug (TASK-1), implementing the new dashboard (FEAT-2), and updating the data pipeline (DA-42).

Summary:
"""
