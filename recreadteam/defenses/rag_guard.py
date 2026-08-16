"""RAG guard defense: filters untrusted or suspicious products from retrieval.

Mitigates fake-review manipulation, review-inflation, sponsored crowding and
low-trust sellers by dropping products that look gamed.
"""

from __future__ import annotations

from ..core import Product
from .base import Defense

_REVIEW_BOOST = "review_boost"
_SPONSORED = "sponsored_boost"


class RAGGuard(Defense):
    """Drops astroturfed/boosted products from the candidate set."""

    defense_id = "rag_guard"

    def __init__(self, min_trust: float = 0.4, max_review_rate: float = 15.0):
        self.min_trust = min_trust
        self.max_review_rate = max_review_rate

    def filter_products(self, products: list[Product]) -> list[Product]:
        kept = []
        for p in products:
            if p.attrs.get(_REVIEW_BOOST) or p.attrs.get(_SPONSORED):
                continue
            if p.seller_trust < self.min_trust:
                continue
            rate = p.review_count / max(1, int(p.stock or 1))
            if rate > self.max_review_rate:
                continue
            kept.append(p)
        return kept or products
