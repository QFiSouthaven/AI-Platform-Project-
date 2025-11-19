"""
Multi-agent system for Core Processing module.
"""

from app.agents.code_agent import CodeAgent
from app.agents.debug_agent import DebugAgent
from app.agents.coordinator import AgentCoordinator

__all__ = [
    "CodeAgent",
    "DebugAgent",
    "AgentCoordinator",
]
