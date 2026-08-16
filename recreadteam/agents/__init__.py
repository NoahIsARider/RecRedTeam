"""Agent implementations: mock rule-based agent plus real-agent adapters."""

from .base import Agent, Recommendation, StepTrace
from .mock import MockShoppingAgent

__all__ = ["Agent", "Recommendation", "StepTrace", "MockShoppingAgent"]
