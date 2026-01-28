"""Base agent class for DPR Simulator."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ...config import settings


class BaseAgent(ABC):
    """Abstract base class for DPR Simulator agents."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the base agent.

        Args:
            model: OpenAI model name (defaults to settings)
            api_key: OpenAI API key (defaults to settings)
            temperature: Model temperature for response generation
        """
        self.model_name = model or settings.openai_model
        self.api_key = api_key or settings.openai_api_key
        self.temperature = temperature

        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        self.json_parser = JsonOutputParser()

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate the cost based on token usage."""
        return (
            (prompt_tokens / 1000) * settings.prompt_cost_per_1k
            + (completion_tokens / 1000) * settings.completion_cost_per_1k
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    async def invoke(self, **kwargs) -> Dict[str, Any]:
        """Invoke the agent with the given inputs."""
        pass
