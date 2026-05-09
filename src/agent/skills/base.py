"""Base interface for agent skills."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class AgentSkill(ABC):
    """Small callable unit owned by the agent."""

    name: str
    description: str

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run the skill and return structured output."""

