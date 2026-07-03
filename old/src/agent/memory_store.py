"""Agent profile, preferences and memory storage."""

import json
from typing import Any, Dict, List

from .config import AGENT_PROFILE_PATH, DEFAULT_AGENT_ID
from .database import agent_db
from .schemas import new_id, utc_ts


DEFAULT_PROFILE = {
    "agent_id": DEFAULT_AGENT_ID,
    "display_name": "QuantAITrade Agent",
    "preferences": {
        "default_run_env": "paper",
        "default_timeframe": "1h",
        "risk_posture": "conservative",
        "requires_human_confirmation": True,
        "max_single_trade_risk_ratio": 0.01,
    },
    "traits": {
        "decision_style": "data_first",
        "review_style": "audit_friendly",
        "execution_boundary": "never_call_exchange_directly",
    },
}


class AgentMemoryStore:
    """Owns durable agent identity, preferences and learned memories."""

    def __init__(self, agent_id: str = DEFAULT_AGENT_ID):
        self.agent_id = agent_id
        AGENT_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        agent_db.init_database()
        self.ensure_profile()

    def ensure_profile(self) -> Dict[str, Any]:
        if not AGENT_PROFILE_PATH.exists():
            AGENT_PROFILE_PATH.write_text(
                json.dumps(DEFAULT_PROFILE, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        profile = self.load_profile()
        conn = agent_db.connect()
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_profile
            (agent_id, display_name, preferences_json, traits_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                profile["agent_id"],
                profile.get("display_name", ""),
                json.dumps(profile.get("preferences", {}), ensure_ascii=False),
                json.dumps(profile.get("traits", {}), ensure_ascii=False),
                utc_ts(),
            ),
        )
        conn.commit()
        return profile

    def load_profile(self) -> Dict[str, Any]:
        return json.loads(AGENT_PROFILE_PATH.read_text(encoding="utf-8"))

    def context(self, limit: int = 10) -> Dict[str, Any]:
        profile = self.load_profile()
        rows = agent_db.connect().execute(
            """
            SELECT memory_id, memory_type, summary, payload_json, importance, created_at
            FROM agent_memories
            WHERE agent_id = ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
            """,
            (self.agent_id, limit),
        ).fetchall()
        memories: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
            memories.append(item)
        return {"profile": profile, "memories": memories}

    def add_memory(
        self,
        summary: str,
        memory_type: str = "lesson",
        payload: Dict[str, Any] | None = None,
        importance: float = 0.5,
    ) -> str:
        memory_id = new_id("mem")
        now = utc_ts()
        agent_db.connect().execute(
            """
            INSERT INTO agent_memories
            (memory_id, agent_id, memory_type, summary, payload_json, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                self.agent_id,
                memory_type,
                summary,
                json.dumps(payload or {}, ensure_ascii=False),
                importance,
                now,
                now,
            ),
        )
        agent_db.connect().commit()
        return memory_id


agent_memory = AgentMemoryStore()

