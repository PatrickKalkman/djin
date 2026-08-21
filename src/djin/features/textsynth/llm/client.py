"""
ABOUTME: LLM client for text synthesis and summarization.
ABOUTME: Uses OpenRouter-hosted models via LangChain to summarize work items.
"""

import os
from typing import List

from loguru import logger

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from djin.common.config import load_config
from djin.common.errors import DjinError
from djin.features.textsynth.llm.prompts import SUMMARIZE_TITLES_PROMPT

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class TextSynthLLMClient:
    """Client for interacting with LLMs for text synthesis operations."""

    def __init__(self, model: str | None = None):
        """
        Initialize the text synthesis LLM client.

        Args:
            model: The OpenRouter model to use; defaults to the "llm.model" setting in config.json
        """
        self.model = model or load_config()["llm"]["model"]

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")

        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            model=self.model,
        )

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

            issues_str = "\n".join(
                [f"- {key}: {title}" if key else f"- {title}" for key, title in zip(keys, titles)]
            )

            prompt_template = PromptTemplate.from_template(SUMMARIZE_TITLES_PROMPT)
            prompt = prompt_template.format(issues=issues_str)

            response = self.llm.invoke(prompt)

            summary = response.content.strip()
            logger.info(f"Generated summary: {summary}")

            return summary
        except Exception as e:
            logger.error(f"Error in summarize_titles_with_keys: {str(e)}")
            raise DjinError(f"Failed to summarize work items: {str(e)}")
