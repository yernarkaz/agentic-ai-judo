"""Base agent class for the agentic AI Judo system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            name: The name of the agent
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Dictionary containing input data to process

        Returns:
            Dictionary containing the processing results
        """
        pass

    def initialize(self) -> None:
        """Initialize the agent's resources and dependencies."""
        self._initialized = True

    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized

    def cleanup(self) -> None:
        """Clean up agent resources."""
        self._initialized = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
