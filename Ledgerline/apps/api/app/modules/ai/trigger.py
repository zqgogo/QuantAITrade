from dataclasses import dataclass
from typing import Literal

TriggerType = Literal["scheduled", "event", "on_demand"]


@dataclass(frozen=True)
class TriggerDefinition:
    trigger_id: str
    trigger_type: TriggerType
    prompt_template_id: str
    output_target: str
    cooldown_minutes: int = 0

