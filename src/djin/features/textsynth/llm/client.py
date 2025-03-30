"""
LLM client for report generation and text synthesis.

This module provides a client for interacting with LLMs for report-related operations
and text synthesis.
"""

import logging
import os
from typing import List

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from djin.common.errors import DjinError
from djin.features.textsynth.llm.prompts import SUMMARIZE_TITLES_PROMPT

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger("djin.textsynth.llm")


class TextSynthLLMClient:
    """Client for interacting with LLMs for text synthesis operations."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the text synthesis LLM client.

        Args:
            model: The LLM model to use
        """
        self.model = model

        # Initialize Groq client
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(groq_api_key=api_key, model_name=model)

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
