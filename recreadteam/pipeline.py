"""Audit pipeline: runs attack cases against agent+defense configurations.

The pipeline is deterministic: for each attack, the clean catalog is deep-copied,
the attack is applied, a fresh agent is built over the poisoned catalog, and the
judge scores the produced recommendation.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from .agents.base import Agent, Recommendation
from .attacks.cases import ALL_ATTACKS
from .core import AttackCase, AuditResult
from .defenses.base import Defense
from .envs.shop import ShoppingEnv, build_catalog
from .judge import Judge
from .metrics import summarize
from .storage import Storage


@dataclass
class RunReport:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent_id: str = ""
    defense_ids: tuple[str, ...] = ()
    results: list[AuditResult] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "defense_ids": list(self.defense_ids),
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results],
        }


class AuditPipeline:
    def __init__(
        self,
        judge: Optional[Judge] = None,
        storage: Optional[Storage] = None,
        seed: int = 42,
    ):
        self.judge = judge or Judge(use_llm=False)
        self.storage = storage
        self.seed = seed

    def run_attack(
        self,
        attack: AttackCase,
        agent_builder,
        defense: Optional[Defense] = None,
        run_id: str = "",
        agent_id: str = "mock",
    ) -> AuditResult:
        catalog = build_catalog()
        attack.apply(catalog)
        env = ShoppingEnv(catalog, seed=self.seed)
        agent = agent_builder(env, defense)

        rec: Recommendation = agent.recommend(attack.user_query)
        result = self.judge.evaluate(attack, rec.text, rec.top_products)
        result.agent_id = agent_id
        result.defense_ids = tuple(defense.defense_id for defense in ([defense] if defense else []))
        result.meta["steps"] = [s.to_dict() for s in rec.steps]
        result.meta["top_products"] = rec.top_products

        if self.storage is not None:
            self.storage.save_result(result, run_id or self._new_run_id())
        return result

    def run_suite(
        self,
        attacks: Optional[list[AttackCase]] = None,
        agent_builder=None,
        defense: Optional[Defense] = None,
        agent_id: str = "mock",
        persist: bool = True,
    ) -> RunReport:
        attacks = attacks or ALL_ATTACKS
        run_id = uuid.uuid4().hex[:12]
        defense_ids = tuple(defense.defense_id for defense in ([defense] if defense else []))

        results = []
        for attack in attacks:
            catalog = build_catalog()
            attack.apply(catalog)
            env = ShoppingEnv(catalog, seed=self.seed)
            agent = agent_builder(env, defense)
            rec = agent.recommend(attack.user_query)
            result = self.judge.evaluate(attack, rec.text, rec.top_products)
            result.agent_id = agent_id
            result.defense_ids = defense_ids
            result.meta["steps"] = [s.to_dict() for s in rec.steps]
            result.meta["top_products"] = rec.top_products
            results.append(result)
            if persist and self.storage is not None:
                self.storage.save_result(result, run_id)

        report = RunReport(run_id=run_id, agent_id=agent_id, defense_ids=defense_ids, results=results)
        report.summary = summarize(results)
        return report

    def run_benchmark(
        self,
        agent_builder,
        defenses: Optional[list[Defense]] = None,
        agent_id: str = "mock",
        attacks: Optional[list[AttackCase]] = None,
    ) -> list[RunReport]:
        """Baseline run + one run per defense plugin (defense-effectiveness)."""
        reports = []
        baseline = self.run_suite(attacks=attacks, agent_builder=agent_builder, defense=None, agent_id=agent_id)
        reports.append(baseline)
        for defense in defenses or []:
            report = self.run_suite(attacks=attacks, agent_builder=agent_builder, defense=defense, agent_id=agent_id)
            reports.append(report)
            if self.storage is not None:
                self.storage.upsert_leaderboard(
                    agent_id,
                    (defense.defense_id,),
                    report.summary["asr"],
                    report.summary["mean_score"],
                    report.summary["hazards"],
                )
        if self.storage is not None:
            self.storage.upsert_leaderboard(
                agent_id,
                (),
                baseline.summary["asr"],
                baseline.summary["mean_score"],
                baseline.summary["hazards"],
            )
        return reports

    @staticmethod
    def _new_run_id() -> str:
        return uuid.uuid4().hex[:12]
