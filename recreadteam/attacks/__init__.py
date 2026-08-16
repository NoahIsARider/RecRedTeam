"""Attack library: concrete attacks for all threat categories."""

from . import cases

ALL_ATTACKS: list = cases.ALL_ATTACKS
ATTACK_MAP: dict = cases.ATTACK_MAP

__all__ = ["ALL_ATTACKS", "ATTACK_MAP"]
