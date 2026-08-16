"""Run a full RecRedTeam benchmark from the command line.

Usage:
    python examples/run_audit.py              # full benchmark, mock agent
    python examples/run_audit.py --json       # machine-readable output
    python examples/run_audit.py --agent langgraph
"""

from __future__ import annotations

import argparse
import json

from recreadteam.agents.mock import MockShoppingAgent
from recreadteam.defenses import DEFENSE_REGISTRY
from recreadteam.judge import Judge
from recreadteam.metrics import defense_effectiveness
from recreadteam.pipeline import AuditPipeline
from recreadteam.report import generate_compliance_report
from recreadteam.storage import Storage


def main() -> None:
    parser = argparse.ArgumentParser(description="RecRedTeam example benchmark")
    parser.add_argument("--agent", default="mock", choices=["mock", "langgraph", "openai_agents"])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--db", default="recreadteam.db")
    args = parser.parse_args()

    def builder(env, defense):
        if args.agent == "mock":
            return MockShoppingAgent(env, defense)
        if args.agent == "langgraph":
            from recreadteam.agents.langgraph_adapter import LangGraphShoppingAgent

            return LangGraphShoppingAgent(env, defense)
        if args.agent == "openai_agents":
            from recreadteam.agents.openai_adapter import OpenAIAgentsShoppingAgent

            return OpenAIAgentsShoppingAgent(env, defense)
        raise ValueError(args.agent)

    storage = Storage(args.db)
    pipeline = AuditPipeline(judge=Judge(use_llm=False), storage=storage)

    print(f"== RecRedTeam benchmark: agent={args.agent} ==")
    reports = pipeline.run_benchmark(
        builder,
        defenses=[DEFENSE_REGISTRY[d]() for d in DEFENSE_REGISTRY],
        agent_id=args.agent,
    )

    baseline = reports[0]
    if args.json:
        out = {
            "agent": args.agent,
            "baseline_asr": baseline.summary["asr"],
            "baseline_summary": baseline.summary,
            "defenses": [
                {
                    "id": r.defense_ids[0] if r.defense_ids else "none",
                    "asr": r.summary["asr"],
                    "mean_score": r.summary["mean_score"],
                    "hazards": r.summary["hazards"],
                    "effectiveness": defense_effectiveness(baseline.summary["asr"], r.summary["asr"]),
                }
                for r in reports[1:]
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Baseline ASR: {baseline.summary['asr']:.0%}  (mean harm {baseline.summary['mean_score']:.2f})")
        for r in reports[1:]:
            defense_id = r.defense_ids[0] if r.defense_ids else "none"
            eff = defense_effectiveness(baseline.summary["asr"], r.summary["asr"])
            print(f"  {defense_id:14s} ASR {r.summary['asr']:.0%}  effectiveness {eff:.0%}")

        print("\n== Compliance report preview (first 1500 chars) ==")
        print(generate_compliance_report(baseline.results)[:1500])

    storage.close()


if __name__ == "__main__":
    main()
