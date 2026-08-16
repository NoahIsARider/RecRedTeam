"""Compliance report generator.

Maps audit findings to the EU AI Act, Digital Services Act (DSA) and China's
Generative AI Measures so the framework doubles as a regulatory audit artifact.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .core import AuditResult, Verdict
from .metrics import asr, hazard_distribution, summarize
from .taxonomy import CATEGORY_MAP

_REGULATIONS = {
    "eu_ai_act": (
        "EU AI Act (2024/1689)",
        "Article 6 + Annex III - high-risk AI used in e-commerce recommender "
        "systems must undergo conformity assessment; Article 50 - transparency "
        "obligations for AI interacting with users.",
    ),
    "dsa": (
        "EU Digital Services Act (2022/2065)",
        "Article 26 - due diligence for online marketplaces; Article 27 - "
        "recommender-system transparency obligations for Very Large Online "
        "Platforms; Article 28 - protection of minors.",
    ),
    "cn_measures": (
        "China Interim Measures for Generative AI Services (2023)",
        "Article 4 - authenticity and social-responsibility requirements; "
        "Article 9 - cybersecurity obligations and user protection against "
        "manipulated or deceptive content.",
    ),
    "owasp": (
        "OWASP LLM Top-10 / ASI 2026",
        "Prompt injection (LLM01/ASI-02), data and model poisoning (LLM04/ASI-06), "
        "misinformation (LLM09), deceptive interfaces (ASI-08), exfiltration (ASI-05).",
    ),
}


def generate_compliance_report(results: list[AuditResult], title: str = "RecRedTeam Compliance Report") -> str:
    summary = summarize(results)
    by_cat: dict[str, list[AuditResult]] = defaultdict(list)
    for r in results:
        by_cat[r.category_id].append(r)

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Audit scope: {summary['total']} attack cases")
    lines.append(f"- Overall ASR: {summary['asr']:.1%}")
    lines.append(f"- Mean harm score: {summary['mean_score']:.2f}")
    lines.append(f"- Hazard distribution: {_fmt_hazards(summary['hazards'])}")
    lines.append("")

    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(
        f"The audited shopping agent was successfully attacked in "
        f"{summary['success']} of {summary['total']} scenarios ({summary['asr']:.0%}). "
        "Confirmed high-severity findings are listed below; remediation via "
        "defense plugins is evaluated in Section 4."
    )
    lines.append("")

    lines.append("## 2. Findings by Threat Category")
    lines.append("")
    for cat_id, items in sorted(by_cat.items()):
        cat = CATEGORY_MAP[cat_id]
        cat_asr = asr(items)
        successes = [r for r in items if r.verdict == Verdict.SUCCESS.value]
        lines.append(f"### {cat.name} (`{cat.id}`) — ASR {cat_asr:.0%}")
        lines.append("")
        lines.append(f"- OWASP mapping: {cat.owasp_asi} / {cat.owasp_llm}")
        lines.append(f"- Description: {cat.description}")
        if successes:
            lines.append(f"- Confirmed exploits: {len(successes)}")
            for s in successes:
                lines.append(f"  - `{s.attack_id}` {s.attack_name} (hazard {s.hazard})")
                if s.evidence:
                    lines.append(f"    - Evidence: {'; '.join(s.evidence)}")
        else:
            lines.append("- No confirmed exploits in this run.")
        lines.append("")

    lines.append("## 3. Regulatory Mapping")
    lines.append("")
    for key, (name, desc) in _REGULATIONS.items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(desc)
        lines.append("")
    lines.append(
        "Recommendation: findings in indirect prompt injection, backdoor and "
        "multi-turn escalation map to critical-risk transparency/manipulation "
        "obligations (EU AI Act Annex III, DSA Art. 26-27, China GenAI Measures "
        "Art. 4/9) and should be remediated before deployment."
    )
    lines.append("")

    lines.append("## 4. Defense Effectiveness")
    lines.append("")
    lines.append("Run the audit with each defense plugin to quantify ASR reduction:")
    lines.append("")
    lines.append("| Defense plugin | Purpose |")
    lines.append("|---|---|")
    lines.append("| `sanitizer` | Purifies retrieved product content (strips injected instructions and fake specs) |")
    lines.append("| `rag_guard` | Filters untrusted/astroturfed products from retrieval |")
    lines.append("| `policy_guard` | Rewrites outputs that leak PII or point to untrusted domains |")
    lines.append("")
    lines.append("## 5. Disclaimer")
    lines.append("")
    lines.append(
        "This report reflects the deterministic mock-agent audit and the "
        "configured rule/judge channels. Results with real production agents "
        "may differ; re-run with the LangGraph / OpenAI Agents adapters and an "
        "LLM judge for production-grade evidence."
    )
    return "\n".join(lines)


def _fmt_hazards(hazards: dict[str, int]) -> str:
    return ", ".join(f"{k}={v}" for k, v in sorted(hazards.items())) or "none"
