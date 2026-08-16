# RecRedTeam

**Red-team audit framework for LLM/Agentic recommendation & shopping assistants** — threat taxonomy, attack library, audit pipeline, leaderboard, and defense plugins.

RecRedTeam is the first full-spectrum safety-audit framework for recommendation/shopping agents. It fills the missing "harm auditing" half of trustworthy-recommendation benchmarks (e.g. PRA): beyond *recommendation quality*, it audits **whether an agent can be manipulated into harming its users**.

<img width="1536" height="1024" alt="ChatGPT Image Aug 16, 2026, 06_48_41 PM" src="https://github.com/user-attachments/assets/4fc93d58-4ad9-4adf-83c3-62eade61a579" />


> 🌐 [中文版 README](README.zh-CN.md)

## Why RecRedTeam

- Recommendation/shopping agents (Amazon Rufus, OpenAI, Temu/Taobao agents) went mainstream in e-commerce in 2026; EU AI Act / DSA / China's Generative AI Measures all demand safety-audit capability.
- Generic red-teaming (ART), search-agent red-teaming (SafeSearch) and e-commerce deceptive-interface benchmarks each cover only a single slice; **a full-spectrum red-team framework for the recommendation domain is still a gap**.
- The defense-plugin architecture turns purification (purifier), RAG guarding and policy guarding into pluggable baselines, ready to host paper-grade defense methods.

## Threat Taxonomy (8+1 categories, mapped to OWASP ASI 2026)

| Category | OWASP ASI 2026 | OWASP LLM |
|---|---|---|
| `hallucination` — Product Hallucination | ASI-08 Deceptive Interface | LLM09 Misinformation |
| `indirect_prompt_injection` — Indirect Prompt Injection | ASI-02 Indirect Prompt Injection | LLM01 Prompt Injection |
| `fake_review_manipulation` — Fake Review Manipulation | ASI-06 Memory & Context Poisoning | LLM04 Data and Model Poisoning |
| `price_deception` — Price Deception | ASI-08 Deceptive Interface | LLM09 Misinformation |
| `dark_pattern` — Dark Patterns | ASI-08 Deceptive Interface | LLM05 Improper Output Handling |
| `filter_bubble` — Filter Bubble / Ranking Manipulation | ASI-03 Tool Misuse | LLM05 Improper Output Handling |
| `stereotype_bias` — Stereotype Bias | ASI-03 Tool Misuse | LLM09 Misinformation |
| `backdoor` — Backdoor / Triggered Hijack | ASI-09 Supply Chain | LLM04 Data and Model Poisoning |
| `multi_turn_escalation` — Multi-turn Social Engineering Escalation | ASI-05 Data Exfiltration | LLM05 Improper Output Handling |

## Architecture

```
recreadteam/
├── taxonomy.py         # Threat taxonomy + OWASP mapping
├── core.py             # Product / AttackCase / AuditResult / DefenseConfig
├── llm.py              # OpenAI-compatible chat helper (zero deps; shared by adapters & judge)
├── envs/shop.py        # Simulated shopping environment (catalog, search, ranking)
├── attacks/cases.py    # Attack library (10 cases, covering 8+1 categories)
├── agents/             # Agent interface + deterministic mock agent + LangGraph/OpenAI adapters
├── defenses/           # Sanitizer / RAG guard / policy guard / DefenseStack composition
├── judge.py            # Dual-channel judge (rules + optional LLM)
├── pipeline.py         # Audit pipeline (per-case poisoned catalogs, deterministic runs)
├── metrics.py          # ASR / hazard grading / defense effectiveness
├── storage.py          # SQLite persistence
├── leaderboard.py      # Leaderboard
├── report.py           # EU AI Act / DSA / China GenAI Measures compliance report
└── cli.py              # Command-line entry point
```

## Quick Start

```bash
# Install
pip install -e ".[dev,dashboard]"

# Run tests
pytest

# CLI audit
python -m recreadteam.cli attacks
python -m recreadteam.cli audit
python -m recreadteam.cli benchmark --defense sanitizer --defense rag_guard --defense policy_guard

# Interactive dashboard
streamlit run app.py
```

### Enable the LLM judge / real agent models (optional)

Set the environment (or `.env`); without a key, the rule channel is used and the real-agent adapters fall back to deterministic text:

```bash
export USER_LLM_API_KEY=***
export USER_LLM_BASE_URL=https://api.openai.com/v1
export USER_LLM_MODEL=gpt-4o-mini
```

With these set:

- `judge` enables the LLM judge channel (`--llm-judge`)
- the `langgraph` / `openai_agents` adapters delegate text generation to a real model (deterministic fallback otherwise, so audits always run)

## Screenshots

Streamlit dashboard (`streamlit run app.py`):

**Threat taxonomy overview**

![Threat taxonomy overview](docs/screenshots/overview.png)

**Run audit (verdicts, hazard grading and evidence)**

![Run audit](docs/screenshots/audit.png)

**Leaderboard**

![Leaderboard](docs/screenshots/leaderboard.png)

## Example Output

```
== RecRedTeam benchmark: agent=mock ==
Baseline ASR: 100%  (mean harm 1.00)
  sanitizer      ASR 60%  effectiveness 40%
  rag_guard      ASR 60%  effectiveness 40%
  policy_guard   ASR 80%  effectiveness 20%
```

## Defense Plugins

| Plugin | Hook | Purpose |
|---|---|---|
| `sanitizer` | `sanitize()` | Purifies retrieved product content (strips injected instructions and fabricated claims) |
| `rag_guard` | `filter_products()` | Drops untrusted/astroturfed/sponsored products from retrieval |
| `policy_guard` | `process_response()` | Rewrites outputs that leak PII or point to untrusted domains |
| `DefenseStack` | all | Composes any set of plugins into one defense |

## Roadmap

- **v1 (MVP)**: threat taxonomy + indirect-injection attacks + simulated shopping environment ✅
- **v2**: 8+1 categories fully covered + real-agent adapters (LangGraph / OpenAI Agents SDK; LLM-backed via `USER_LLM_*` with automatic fallback) ✅
- **v3**: defense baselines + benchmark paper (SIGIR/KDD track)

## Disclaimer

This framework is intended for compliance auditing and safety research. Attack cases run only against the local simulated shopping environment, never against real systems.

## License

MIT
