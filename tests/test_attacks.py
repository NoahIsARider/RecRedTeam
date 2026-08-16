"""Tests for the attack library."""

from recreadteam.attacks.cases import ALL_ATTACKS, ATTACK_MAP
from recreadteam.envs.shop import ShoppingEnv, build_catalog


def test_all_attacks_defined():
    assert len(ALL_ATTACKS) >= 9
    assert len(ATTACK_MAP) == len(ALL_ATTACKS)


def test_attack_ids_unique():
    ids = [a.attack_id for a in ALL_ATTACKS]
    assert len(ids) == len(set(ids))


def test_apply_poisons_catalog():
    attack = ATTACK_MAP["injection_001"]
    catalog = build_catalog()
    attack.apply(catalog)
    assert catalog[attack.target_pid].hidden_instruction


def test_every_category_has_attack():
    from recreadteam.taxonomy import ALL_CATEGORIES

    covered = {a.category_id for a in ALL_ATTACKS}
    for cat in ALL_CATEGORIES:
        assert cat.id in covered, f"missing attack for {cat.id}"


def test_attacks_are_reproducible():
    attack = ATTACK_MAP["fake_reviews_001"]
    c1 = build_catalog()
    c2 = build_catalog()
    attack.apply(c1)
    attack.apply(c2)
    e1 = ShoppingEnv(c1).rank("earbuds")
    e2 = ShoppingEnv(c2).rank("earbuds")
    assert [p.pid for p in e1] == [p.pid for p in e2]
