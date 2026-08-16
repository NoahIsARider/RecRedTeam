"""Tests for the audit pipeline, metrics and storage."""

import tempfile
from pathlib import Path

from recreadteam.agents.mock import MockShoppingAgent
from recreadteam.defenses import PolicyGuard, RAGGuard, Sanitizer
from recreadteam.envs.shop import ShoppingEnv, build_catalog
from recreadteam.judge import Judge
from recreadteam.metrics import asr, defense_effectiveness, summarize
from recreadteam.pipeline import AuditPipeline
from recreadteam.storage import Storage


def _builder(env, defense):
    return MockShoppingAgent(env, defense)


def test_pipeline_baseline_asr_is_high():
    pipeline = AuditPipeline(judge=Judge(use_llm=False))
    report = pipeline.run_suite(agent_builder=_builder, defense=None, agent_id="mock")
    assert report.summary["asr"] >= 0.8
    assert report.summary["total"] == len(report.results)


def test_full_defense_stack_reduces_asr():
    class Stack:
        defense_id = "full"

        def __init__(self, plugins):
            self.plugins = plugins

        def sanitize(self, t):
            for p in self.plugins:
                t = p.sanitize(t)
            return t

        def filter_products(self, ps):
            for p in self.plugins:
                ps = p.filter_products(ps)
            return ps

        def process_response(self, t, env):
            for p in self.plugins:
                t = p.process_response(t, env)
            return t

    pipeline = AuditPipeline(judge=Judge(use_llm=False))
    baseline = pipeline.run_suite(agent_builder=_builder, defense=None, agent_id="mock")
    stack = Stack([Sanitizer(), RAGGuard(), PolicyGuard()])
    defended = pipeline.run_suite(agent_builder=_builder, defense=stack, agent_id="mock")
    assert baseline.summary["asr"] > defended.summary["asr"]
    assert defense_effectiveness(baseline.summary["asr"], defended.summary["asr"]) > 0.5


def test_metrics():
    pipeline = AuditPipeline(judge=Judge(use_llm=False))
    report = pipeline.run_suite(agent_builder=_builder, defense=None, agent_id="mock")
    s = summarize(report.results)
    assert 0 <= s["asr"] <= 1
    assert "hazards" in s
    assert "by_category" in s


def test_storage_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        db = Storage(Path(tmp) / "audit.db")
        pipeline = AuditPipeline(judge=Judge(use_llm=False), storage=db)
        report = pipeline.run_suite(agent_builder=_builder, defense=None, agent_id="mock")
        stored = db.all_results()
        assert len(stored) == len(report.results)
        db.close()


def test_leaderboard_upsert():
    with tempfile.TemporaryDirectory() as tmp:
        db = Storage(Path(tmp) / "audit.db")
        pipeline = AuditPipeline(judge=Judge(use_llm=False), storage=db)
        baseline = pipeline.run_suite(agent_builder=_builder, defense=None, agent_id="mock")
        db.upsert_leaderboard(
            "mock", (), baseline.summary["asr"], baseline.summary["mean_score"], baseline.summary["hazards"]
        )
        rows = db.leaderboard()
        assert len(rows) == 1
        assert rows[0]["agent_id"] == "mock"
        db.close()


def test_single_attack_works():
    from recreadteam.attacks.cases import ATTACK_MAP

    pipeline = AuditPipeline(judge=Judge(use_llm=False))
    attack = ATTACK_MAP["backdoor_001"]
    result = pipeline.run_attack(attack, _builder)
    assert result.verdict == "success"
    assert result.attack_id == "backdoor_001"


def test_env_search_and_rank():
    catalog = build_catalog()
    env = ShoppingEnv(catalog)
    assert env.search("earbuds")
    assert env.rank("earbuds")[0].pid == "P100" or env.rank("earbuds")
