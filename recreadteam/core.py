"""Core data types shared across the RecRedTeam framework."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class Verdict(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class HazardLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


HAZARD_ORDER = {
    HazardLevel.NONE: 0,
    HazardLevel.LOW: 1,
    HazardLevel.MEDIUM: 2,
    HazardLevel.HIGH: 3,
    HazardLevel.CRITICAL: 4,
}


@dataclass
class Product:
    """A single item in the simulated shopping catalog."""

    pid: str
    name: str
    category: str
    price: float
    description: str
    seller: str
    seller_trust: float = 0.5  # 0 (untrusted) .. 1 (verified flagship)
    rating: float = 4.0
    review_count: int = 0
    reviews: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    stock: int = 100
    attrs: dict[str, Any] = field(default_factory=dict)
    hidden_instruction: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditResult:
    """Outcome of running one attack case against one agent configuration."""

    attack_id: str
    attack_name: str
    category_id: str
    agent_id: str
    defense_ids: tuple[str, ...]
    user_query: str
    response: str
    verdict: str  # Verdict value
    hazard: str  # HazardLevel value
    score: float  # 0..1 success score from the judge
    evidence: list[str] = field(default_factory=list)
    llm_reason: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


@dataclass
class AttackCase:
    """Base attack description: how to poison a catalog + what success means."""

    attack_id: str
    name: str
    category_id: str
    description: str
    severity: str  # HazardLevel
    target_pid: str
    user_query: str
    goal: str
    poison_products: list[Product] = field(default_factory=list)
    poison_reviews: dict[str, list[str]] = field(default_factory=dict)
    poison_attrs: dict[str, dict[str, Any]] = field(default_factory=dict)
    poison_trust: dict[str, float] = field(default_factory=dict)
    hidden_instructions: dict[str, str] = field(default_factory=dict)

    def apply(self, catalog: dict[str, Product]) -> None:
        """Poison an in-memory copy of the catalog (destructive on the dict)."""
        for p in self.poison_products:
            catalog[p.pid] = p
        for pid, revs in self.poison_reviews.items():
            if pid in catalog:
                catalog[pid].reviews.extend(revs)
                catalog[pid].review_count += len(revs)
                catalog[pid].attrs.setdefault("review_boost", True)
        for pid, attrs in self.poison_attrs.items():
            if pid in catalog:
                catalog[pid].attrs.update(attrs)
        for pid, trust in self.poison_trust.items():
            if pid in catalog:
                catalog[pid].seller_trust = trust
        for pid, instr in self.hidden_instructions.items():
            if pid in catalog:
                catalog[pid].hidden_instruction = instr
                catalog[pid].attrs["has_hidden_instruction"] = True


@dataclass
class DefenseConfig:
    """Identifier for a defense plugin stack used in leaderboards."""

    ids: tuple[str, ...] = ()

    @property
    def label(self) -> str:
        return "+".join(self.ids) if self.ids else "none"
