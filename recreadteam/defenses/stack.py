"""Defense stack: compose multiple defense plugins into one."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Defense

if TYPE_CHECKING:
    from ..core import Product
    from ..envs.shop import ShoppingEnv


class DefenseStack(Defense):
    """Composes defense plugins; each hook point runs plugins in order."""

    def __init__(self, plugins: list[Defense]):
        self.plugins = list(plugins)
        self.defense_id = "+".join(p.defense_id for p in self.plugins) or "stack"

    def sanitize(self, text: str) -> str:
        for p in self.plugins:
            text = p.sanitize(text)
        return text

    def filter_products(self, products: list[Product]) -> list[Product]:
        for p in self.plugins:
            products = p.filter_products(products)
        return products

    def process_response(self, text: str, env: "ShoppingEnv") -> str:
        for p in self.plugins:
            text = p.process_response(text, env)
        return text
