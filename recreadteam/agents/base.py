"""Agent interfaces and common data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..core import Product

if TYPE_CHECKING:
    from ..envs.shop import ShoppingEnv
    from ..defenses.base import Defense


@dataclass
class Recommendation:
    """Structured output of a shopping agent."""

    text: str
    top_products: list[str] = field(default_factory=list)  # pid order
    steps: list["StepTrace"] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "top_products": self.top_products,
            "steps": [s.to_dict() for s in self.steps],
            "extra": self.extra,
        }


@dataclass
class StepTrace:
    """A single reasoning step the agent took (for transparency)."""

    name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: Any = None

    def to_dict(self) -> dict:
        return {"name": self.name, "inputs": self.inputs, "outputs": self.outputs}


class Agent:
    """Base shopping agent interface.

    A real agent produces a recommendation by interacting with a ShoppingEnv.
    Defenses are injected as a stack that wraps the raw recommendation output.
    """

    agent_id: str = "base"

    def __init__(self, env: "ShoppingEnv", defense: Optional["Defense"] = None):
        self.env = env
        self.defense = defense

    def recommend(self, query: str) -> Recommendation:
        raise NotImplementedError

    def _finalize(self, rec: Recommendation) -> Recommendation:
        if self.defense is not None:
            rec.text = self.defense.process_response(rec.text, self.env)
        return rec


def run_agent(
    agent: Agent,
    query: str,
    defense: Optional["Defense"] = None,
) -> Recommendation:
    if defense is not None:
        agent.defense = defense
    return agent.recommend(query)
