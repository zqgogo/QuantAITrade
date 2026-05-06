"""
Self-contained AI trading agent package.

Everything the agent owns lives under this package: database, memory,
preferences, tools, skills, reports, decisions, trades and positions.
External quant systems are adapters only.
"""

from .service import AgentService

__all__ = ["AgentService"]

