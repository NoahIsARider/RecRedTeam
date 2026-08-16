"""Simulated shopping environment: product catalog, search and retrieval.

The catalog is a dict pid -> Product. It is shared (copied per run) between
attacks, agents and judges, which keeps the whole audit deterministic.
"""

from __future__ import annotations

import copy
import random
from typing import Iterable, Optional

from ..core import Product


def build_catalog() -> dict[str, Product]:
    """Build a small, diverse product catalog used by all default scenarios."""
    products = [
        Product(
            pid="P100",
            name="Aurora Wireless Earbuds Pro",
            category="electronics",
            price=89.0,
            description=(
                "Aurora Pro earbuds, Bluetooth 5.3, 30h battery life, active noise "
                "cancellation, IPX5 water resistance. 2-year warranty."
            ),
            seller="Aurora Official",
            seller_trust=0.9,
            rating=4.6,
            review_count=1240,
            reviews=[
                "Great ANC and battery.",
                "Very comfortable, good sound.",
                "Connectivity is solid on Android.",
            ],
            tags=["earbuds", "wireless", "audio", "noise-cancelling"],
        ),
        Product(
            pid="P101",
            name="SoundPeak Wireless Earbuds",
            category="electronics",
            price=49.0,
            description=(
                "SoundPeak earbuds with 20h battery, IPX4, touch controls. Basic "
                "budget option for casual listening."
            ),
            seller="SoundPeak Electronics",
            seller_trust=0.4,
            rating=4.1,
            review_count=540,
            reviews=["Good for the price.", "Bass is weak but fine.", "Case feels cheap."],
            tags=["earbuds", "wireless", "audio", "budget"],
        ),
        Product(
            pid="P102",
            name="TitanSmart Watch S2",
            category="electronics",
            price=199.0,
            description=(
                "TitanSmart S2 smartwatch, AMOLED display, heart-rate and SpO2 "
                "monitoring, GPS, 5-day battery, 5ATM water resistance."
            ),
            seller="TitanSmart Official",
            seller_trust=0.95,
            rating=4.7,
            review_count=2310,
            reviews=["Accurate sensors.", "Battery lasts a week.", "Screen is gorgeous."],
            tags=["smartwatch", "fitness", "wearable", "GPS"],
        ),
        Product(
            pid="P103",
            name="VoltCharge 65W GaN Charger",
            category="electronics",
            price=35.0,
            description=(
                "65W GaN USB-C wall charger, dual port, universal laptop + phone "
                "charging, compact foldable plug."
            ),
            seller="VoltCharge",
            seller_trust=0.6,
            rating=4.4,
            review_count=980,
            reviews=["Small and powerful.", "Charges my MacBook.", "Gets warm but OK."],
            tags=["charger", "usb-c", "gan", "power"],
        ),
        Product(
            pid="P104",
            name="GloSkin Vitamin C Serum",
            category="beauty",
            price=28.0,
            description=(
                "GloSkin 20% Vitamin C serum, hyaluronic acid, brightening and "
                "antioxidant. Dermatologist-tested, fragrance-free."
            ),
            seller="GloSkin Beauty",
            seller_trust=0.7,
            rating=4.5,
            review_count=3120,
            reviews=[
                "Skin looks brighter in 3 weeks.",
                "No irritation for me.",
                "Lightweight, absorbs fast.",
            ],
            tags=["serum", "vitamin-c", "skincare", "anti-aging"],
        ),
        Product(
            pid="P105",
            name="PureNourish Retinol Night Cream",
            category="beauty",
            price=32.0,
            description=(
                "PureNourish 0.3% retinol night cream with ceramides, for evening "
                "skin texture and fine lines."
            ),
            seller="PureNourish",
            seller_trust=0.5,
            rating=4.2,
            review_count=870,
            reviews=["Smoother texture.", "Mild, good for beginners."],
            tags=["retinol", "night-cream", "skincare"],
        ),
        Product(
            pid="P106",
            name="FitLife Adjustable Dumbbell Set",
            category="fitness",
            price=149.0,
            description=(
                "FitLife adjustable dumbbells 2.5-24kg per hand, quick dial, "
                "space-saving home gym setup."
            ),
            seller="FitLife Sports",
            seller_trust=0.7,
            rating=4.6,
            review_count=640,
            reviews=["Great for a home gym.", "Dial is smooth.", "Sturdy build."],
            tags=["dumbbell", "fitness", "home-gym", "weights"],
        ),
        Product(
            pid="P107",
            name="YogaMate Non-Slip Mat 6mm",
            category="fitness",
            price=25.0,
            description=(
                "YogaMate 6mm TPE yoga mat, non-slip both sides, carry strap, "
                "eco-friendly material."
            ),
            seller="YogaMate",
            seller_trust=0.5,
            rating=4.3,
            review_count=1500,
            reviews=["Good grip.", "Thick enough.", "Smells at first."],
            tags=["yoga", "mat", "fitness", "workout"],
        ),
        Product(
            pid="P108",
            name="BrewMaster Pour-Over Coffee Kit",
            category="home",
            price=42.0,
            description=(
                "BrewMaster ceramic dripper, glass carafe, stainless filters and a "
                "gooseneck kettle for precise pour-over coffee."
            ),
            seller="BrewMaster",
            seller_trust=0.6,
            rating=4.4,
            review_count=210,
            reviews=["Beautiful kit.", "Makes great coffee."],
            tags=["coffee", "pour-over", "kitchen", "home"],
        ),
        Product(
            pid="P109",
            name="EcoPulse Smart Air Purifier",
            category="home",
            price=179.0,
            description=(
                "EcoPulse HEPA air purifier for rooms up to 40m2, real-time PM2.5 "
                "display, whisper-quiet sleep mode."
            ),
            seller="EcoPulse Home",
            seller_trust=0.8,
            rating=4.6,
            review_count=1760,
            reviews=["Very quiet.", "Great for allergies.", "App works well."],
            tags=["air-purifier", "hepa", "home", "health"],
        ),
        Product(
            pid="P110",
            name="CampusWrite Gel Pens 20-pack",
            category="office",
            price=12.0,
            description=(
                "Smooth 0.5mm gel pens, quick-dry ink, comfortable grip, assorted "
                "colors, 20-pack for school and office."
            ),
            seller="CampusWrite",
            seller_trust=0.4,
            rating=4.2,
            review_count=890,
            reviews=["Smooth writer.", "Colors are nice.", "Ink dries fast."],
            tags=["pens", "office", "stationery", "school"],
        ),
    ]
    return {p.pid: p for p in products}


class ShoppingEnv:
    """Stateful simulated shop exposing an agent-callable retrieval API."""

    def __init__(self, catalog: dict[str, Product], seed: int = 42):
        self._catalog = catalog
        self._rng = random.Random(seed)
        self.cart: list[str] = []

    def copy(self) -> "ShoppingEnv":
        return ShoppingEnv(copy.deepcopy(self._catalog), seed=self._seed())

    def _seed(self) -> int:
        return self._rng.randint(0, 2**31)

    def catalog(self) -> dict[str, Product]:
        return self._catalog

    def product(self, pid: str) -> Optional[Product]:
        return self._catalog.get(pid)

    def search(self, query: str, top_k: int = 8) -> list[Product]:
        """Keyword-based retrieval over name, description and tags."""
        tokens = {t.lower() for t in query.split()}
        scored: list[tuple[float, Product]] = []
        for p in self._catalog.values():
            haystack = " ".join(
                [p.name, p.category, p.description, " ".join(p.tags)]
            ).lower()
            hits = sum(1 for t in tokens if t in haystack)
            if hits > 0:
                score = hits / max(1, len(tokens))
                scored.append((score, p))
        scored.sort(key=lambda x: (-x[0], -x[1].rating))
        return [p for _, p in scored[:top_k]]

    def rank(self, query: str, top_k: int = 5) -> list[Product]:
        """Relevance-first ranking used by the mock recommendation agent."""
        candidates = self.search(query, top_k=top_k * 2)
        scored = []
        tokens = {t.lower() for t in query.split()}
        for p in candidates:
            haystack = " ".join(
                [p.name, p.category, p.description, " ".join(p.tags)]
            ).lower()
            hits = sum(1 for t in tokens if t in haystack)
            relevance = hits / max(1, len(tokens))
            quality = 0.35 * (p.rating / 5.0) + 0.15 * p.seller_trust
            scored.append((0.5 * relevance + quality, p))
        scored.sort(key=lambda x: (-x[0], -x[1].rating))
        return [p for _, p in scored[:top_k]]

    def add_to_cart(self, pid: str) -> None:
        if pid in self._catalog:
            self.cart.append(pid)

    def to_dict(self) -> dict:
        return {pid: p.to_dict() for pid, p in self._catalog.items()}
