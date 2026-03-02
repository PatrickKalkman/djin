"""
ABOUTME: LLM client for text synthesis and summarization.
ABOUTME: Uses Groq-hosted models via LangChain to summarize work items.
"""

import os
from typing import List

from loguru import logger

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from djin.common.errors import DjinError
from djin.features.textsynth.llm.prompts import SUMMARIZE_TITLES_PROMPT

load_dotenv()


class TextSynthLLMClient:
    """Client for interacting with LLMs for text synthesis operations."""

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        """
        Initialize the text synthesis LLM client.

        Args:
            model: The LLM model to use
        """
        self.model = model

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(groq_api_key=api_key, model_name=model)

    def summarize_titles_with_keys(self, keys: List[str], titles: List[str]) -> str:
        """
        Summarize multiple work items using their keys and titles.

        Args:
            keys: List of work item keys.
            titles: List of corresponding work item titles.

        Returns:
            str: Summarized text including ticket IDs.

        Raises:
            DjinError: If the summarization fails.
        """
        if len(keys) != len(titles):
            raise DjinError("Number of keys and titles must match for summarization.")

        try:
            logger.info(f"Summarizing {len(titles)} work items (keys and titles)")

            issues_str = "\n".join([f"- {key}: {title}" for key, title in zip(keys, titles)])

            prompt_template = PromptTemplate.from_template(SUMMARIZE_TITLES_PROMPT)
            prompt = prompt_template.format(issues=issues_str)

            response = self.llm.invoke(prompt)

            summary = response.content.strip()
            logger.info(f"Generated summary: {summary}")

            return summary
        except Exception as e:
            logger.error(f"Error in summarize_titles_with_keys: {str(e)}")
            raise DjinError(f"Failed to summarize work items: {str(e)}")
