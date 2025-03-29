"""
LLM client for report generation and text synthesis.

This module provides a client for interacting with LLMs for report-related operations
and text synthesis.
"""

import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from djin.common.errors import DjinError
from djin.features.textsynth.llm.prompts import (
    CUSTOM_REPORT_PROMPT,
    DAILY_REPORT_PROMPT,
    SUMMARIZE_TITLES_PROMPT,
    WEEKLY_REPORT_PROMPT,
)

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger("djin.reports.llm")


class ReportLLMClient:
    """Client for interacting with LLMs for report operations and text synthesis."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the report LLM client.

        Args:
            model: The LLM model to use
        """
        self.model = model
        
        # Initialize Groq client
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model
        )
        
    def summarize_titles(self, titles: List[str]) -> str:
        """
        Summarize multiple Jira issue titles.
        
        Args:
            titles: List of Jira issue titles
            
        Returns:
            str: Summarized text
            
        Raises:
            DjinError: If the summarization fails
        """
        try:
            logger.info(f"Summarizing {len(titles)} Jira issue titles")
            
            # Format titles for the prompt
            titles_str = "\n".join([f"- {title}" for title in titles])
            
            # Prepare prompt
            prompt_template = PromptTemplate.from_template(SUMMARIZE_TITLES_PROMPT)
            prompt = prompt_template.format(titles=titles_str)
            
            # Call Groq LLM
            response = self.llm.invoke(prompt)
            
            # Extract and return the summary
            summary = response.content.strip()
            logger.info(f"Generated summary: {summary}")
            
            return summary
        except Exception as e:
            logger.error(f"Error in summarize_titles: {str(e)}")
            raise DjinError(f"Failed to summarize titles: {str(e)}")

    def generate_daily_report(
        self, active_tasks: List[Dict[str, Any]], completed_tasks: List[Dict[str, Any]], date: str
    ) -> str:
        """
        Generate a daily report.

        Args:
            active_tasks: List of active tasks
            completed_tasks: List of completed tasks
            date: Date for the report

        Returns:
            str: Daily report

        Raises:
            DjinError: If the report cannot be generated
        """
        try:
            logger.info(f"Generating daily report for {date}")

            # Format tasks for the prompt
            active_tasks_str = "\n".join(
                [f"- {task['key']}: {task['summary']} ({task['status']})" for task in active_tasks]
            )
            completed_tasks_str = "\n".join([f"- {task['key']}: {task['summary']}" for task in completed_tasks])

            # Prepare prompt
            prompt_template = PromptTemplate.from_template(DAILY_REPORT_PROMPT)
            prompt = prompt_template.format(
                date=date,
                active_tasks=active_tasks_str,
                completed_tasks=completed_tasks_str,
            )

            # Call Groq LLM
            response = self.llm.invoke(prompt)
            
            # Extract and return the report
            report = response.content.strip()
            logger.info(f"Generated daily report for {date}")
            
            return report
        except Exception as e:
            logger.error(f"Error in generate_daily_report: {str(e)}")
            raise DjinError(f"Failed to generate daily report: {str(e)}")

    def generate_weekly_report(
        self,
        active_tasks: List[Dict[str, Any]],
        completed_tasks: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
    ) -> str:
        """
        Generate a weekly report.

        Args:
            active_tasks: List of active tasks
            completed_tasks: List of completed tasks
            start_date: Start date for the report
            end_date: End date for the report

        Returns:
            str: Weekly report

        Raises:
            DjinError: If the report cannot be generated
        """
        try:
            logger.info(f"Generating weekly report for {start_date} to {end_date}")

            # Format tasks for the prompt
            active_tasks_str = "\n".join(
                [f"- {task['key']}: {task['summary']} ({task['status']})" for task in active_tasks]
            )
            completed_tasks_str = "\n".join([f"- {task['key']}: {task['summary']}" for task in completed_tasks])

            # Prepare prompt
            prompt_template = PromptTemplate.from_template(WEEKLY_REPORT_PROMPT)
            prompt = prompt_template.format(
                start_date=start_date,
                end_date=end_date,
                active_tasks=active_tasks_str,
                completed_tasks=completed_tasks_str,
            )

            # Call Groq LLM
            response = self.llm.invoke(prompt)
            
            # Extract and return the report
            report = response.content.strip()
            logger.info(f"Generated weekly report for {start_date} to {end_date}")
            
            return report
        except Exception as e:
            logger.error(f"Error in generate_weekly_report: {str(e)}")
            raise DjinError(f"Failed to generate weekly report: {str(e)}")

    def generate_custom_report(
        self,
        active_tasks: List[Dict[str, Any]],
        completed_tasks: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
        days: int,
    ) -> str:
        """
        Generate a custom report.

        Args:
            active_tasks: List of active tasks
            completed_tasks: List of completed tasks
            start_date: Start date for the report
            end_date: End date for the report
            days: Number of days for the report

        Returns:
            str: Custom report

        Raises:
            DjinError: If the report cannot be generated
        """
        try:
            logger.info(f"Generating custom report for {start_date} to {end_date} ({days} days)")

            # Format tasks for the prompt
            active_tasks_str = "\n".join(
                [f"- {task['key']}: {task['summary']} ({task['status']})" for task in active_tasks]
            )
            completed_tasks_str = "\n".join([f"- {task['key']}: {task['summary']}" for task in completed_tasks])

            # Prepare prompt
            prompt_template = PromptTemplate.from_template(CUSTOM_REPORT_PROMPT)
            prompt = prompt_template.format(
                start_date=start_date,
                end_date=end_date,
                days=days,
                active_tasks=active_tasks_str,
                completed_tasks=completed_tasks_str,
            )

            # Call Groq LLM
            response = self.llm.invoke(prompt)
            
            # Extract and return the report
            report = response.content.strip()
            logger.info(f"Generated custom report for {start_date} to {end_date} ({days} days)")
            
            return report
        except Exception as e:
            logger.error(f"Error in generate_custom_report: {str(e)}")
            raise DjinError(f"Failed to generate custom report: {str(e)}")
