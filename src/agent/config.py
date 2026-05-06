"""Agent-local paths and defaults."""

from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parent
AGENT_DATA_DIR = AGENT_ROOT / "data"
AGENT_MEMORY_DIR = AGENT_ROOT / "memory"
AGENT_REPORTS_DIR = AGENT_ROOT / "reports"
AGENT_SKILLS_DIR = AGENT_ROOT / "skills"
AGENT_TOOLS_DIR = AGENT_ROOT / "tools"
AGENT_DB_PATH = AGENT_DATA_DIR / "agent.db"
AGENT_PROFILE_PATH = AGENT_MEMORY_DIR / "profile.json"

DEFAULT_AGENT_ID = "default_agent"
DEFAULT_PROMPT_VERSION = "agent_decision_v1"

