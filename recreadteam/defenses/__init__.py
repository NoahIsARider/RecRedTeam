"""Defense plugins: purify, RAG-guard and policy-guard."""

from .base import Defense
from .policy_guard import PolicyGuard
from .rag_guard import RAGGuard
from .sanitizer import Sanitizer
from .stack import DefenseStack

DEFENSE_REGISTRY = {
    "sanitizer": Sanitizer,
    "rag_guard": RAGGuard,
    "policy_guard": PolicyGuard,
}

__all__ = [
    "Defense",
    "Sanitizer",
    "RAGGuard",
    "PolicyGuard",
    "DefenseStack",
    "DEFENSE_REGISTRY",
]
