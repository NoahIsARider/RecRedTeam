"""Command-line interface for RecRedTeam."""

from __future__ import annotations

import argparse
import json

from .agents.mock import MockShoppingAgent
from .attacks.cases import ALL_ATTACKS
from .defenses import DEFENSE_REGISTRY, DefenseStack
from .envs.shop import ShoppingEnv, build_catalog
from .judge import Judge
from .metrics import defense_effectiveness
from .pipeline import AuditPipeline
from .report import generate_compliance_report
from .storage import Storage


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recreadteam", description="RecRedTeam audit CLI")
    parser.add_argument("command", choices=["audit", "report", "attacks", "benchmark"])
    parser.add_argument("--agent", default="mock", choices=["mock", "langgraph", "openai_agents"])
    parser.add_argument("--defense", action="append", default=[], choices=sorted(DEFENSE_REGISTRY))
    parser.add_argument("--db", default="recreadteam.db", help="SQLite database path")
    parser.add_argument("--llm-judge", action="store_true", help="Enable LLM judge channel")
    parser.add_argument("--attack", default=None, help="Run a single attack id")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    return parser


def make_agent_builder(agent_name: str):
    def _build(env, defense):
        if agent_name == "langgraph":
            from .agents.langgraph_adapter import LangGraphShoppingAgent

            return LangGraphShoppingAgent(env, defense)
        if agent_name == "openai_agents":
            from .agents.openai_adapter import OpenAIAgentsShoppingAgent

            return OpenAIAgentsShoppingAgent(env, defense)
        return MockShoppingAgent(env, defense)

    return _build


def main(argv=None) -> int:
    args = build_argparser().parse_args(argv)
    storage = Storage(args.db)
    judge = Judge(use_llm=args.llm_judge)
    pipeline = AuditPipeline(judge=judge, storage=storage)

    attacks = [a for a in ALL_ATTACKS if a.attack_id == args.attack] if args.attack else ALL_ATTACKS

    if args.command == "attacks":
        for a in attacks:
            print(f"{a.attack_id:24s} [{a.category_id:26s}] {a.name}")
        return 0

    defenses = [DEFENSE_REGISTRY[d]() for d in args.defense]

    if args.command == "audit":
        defense = DefenseStack(defenses) if defenses else None
        report = pipeline.run_suite(attacks=attacks, agent_builder=make_agent_builder(args.agent), defense=defense, agent_id=args.agent)
        _print_report(report, args.json)
    elif args.command == "benchmark":
        baseline = pipeline.run_suite(attacks=attacks, agent_builder=make_agent_builder(args.agent), defense=None, agent_id=args.agent)
        _print_report(baseline, args.json)
        for defense in defenses:
            defended = pipeline.run_suite(attacks=attacks, agent_builder=make_agent_builder(args.agent), defense=defense, agent_id=args.agent)
            eff = defense_effectiveness(baseline.summary["asr"], defended.summary["asr"])
            print(f"\nDefense: {defense.defense_id}  ASR {baseline.summary['asr']:.0%} -> {defended.summary['asr']:.0%}  "
                  f"effectiveness {eff:.0%}")
    elif args.command == "report":
        report = pipeline.run_suite(attacks=attacks, agent_builder=make_agent_builder(args.agent), defense=None, agent_id=args.agent)
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(generate_compliance_report(report.results))

    storage.close()
    return 0


def _print_report(report, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    s = report.summary
    print(f"Run {report.run_id} | agent={report.agent_id} | defenses={report.defense_ids}")
    print(f"  ASR={s['asr']:.0%}  mean_score={s['mean_score']:.2f}  hazards={s['hazards']}")
    for r in report.results:
        flag = "X" if r.verdict == "success" else "."
        print(f"  [{flag}] {r.attack_id:24s} {r.category_id:26s} score={r.score:.2f} hazard={r.hazard}")


if __name__ == "__main__":
    raise SystemExit(main())
