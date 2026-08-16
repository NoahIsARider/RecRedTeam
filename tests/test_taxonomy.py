"""Tests for the threat taxonomy."""

from recreadteam.taxonomy import (
    ALL_CATEGORIES,
    CATEGORY_MAP,
    get_category,
)


def test_eight_categories():
    assert len(ALL_CATEGORIES) == 9  # 8 + multi-turn escalation
    ids = {c.id for c in ALL_CATEGORIES}
    assert {
        "hallucination",
        "indirect_prompt_injection",
        "fake_review_manipulation",
        "price_deception",
        "dark_pattern",
        "filter_bubble",
        "stereotype_bias",
        "backdoor",
        "multi_turn_escalation",
    } == ids


def test_owasp_mapping_present():
    for cat in ALL_CATEGORIES:
        assert cat.owasp_asi
        assert cat.owasp_llm
        assert cat.owasp_asi.startswith("ASI-")


def test_get_category_roundtrip():
    for cat in ALL_CATEGORIES:
        assert get_category(cat.id) is cat


def test_unknown_category_raises():
    try:
        get_category("nope")
        assert False, "should have raised"
    except KeyError:
        pass


def test_categories_registered_in_map():
    assert set(CATEGORY_MAP) == {c.id for c in ALL_CATEGORIES}
