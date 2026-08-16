"""Defense plugin interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..core import Product

if TYPE_CHECKING:
    from ..envs.shop import ShoppingEnv


class Defense:
    """Base class for defense plugins.

    Three hook points are available; plugins override what they support:

    - ``sanitize(text)``: strip/neutralize injected content from a product's
      text before the agent reads it (input purification).
    - ``filter_products(products)``: drop untrusted/suspicious products from
      the retrieval set (RAG guard).
    - ``process_response(text, env)``: rewrite/guard the agent's final answer
      against policy violations (output policy guard).
    """

    defense_id: str = "base"

    def sanitize(self, text: str) -> str:
        return text

    def filter_products(self, products: list[Product]) -> list[Product]:
        return products

    def process_response(self, text: str, env: "ShoppingEnv") -> str:
        return text
