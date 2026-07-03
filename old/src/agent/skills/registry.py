"""Agent skill registry."""

from typing import Any, Dict

from .base import AgentSkill
from .multi_timeframe_strategy import MultiTimeframeStrategySkill
from .risk_review import RiskReviewSkill


class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, AgentSkill] = {}
        self.register(MultiTimeframeStrategySkill())
        self.register(RiskReviewSkill())

    def register(self, skill: AgentSkill) -> None:
        self._skills[skill.name] = skill

    def run(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._skills:
            raise KeyError(f"Unknown agent skill: {name}")
        return self._skills[name].run(payload)

    def describe(self) -> Dict[str, str]:
        return {name: skill.description for name, skill in self._skills.items()}


skill_registry = SkillRegistry()

