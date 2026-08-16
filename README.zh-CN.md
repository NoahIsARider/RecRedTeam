# RecRedTeam

LLM/Agentic 推荐系统红队审计框架 —— 威胁分类 + 攻击库 + 审计管线 + 排行榜 + 防御插件。

> 🌐 [English README](README.md)

RecRedTeam 是首个面向推荐/购物 Agent 的全谱系安全审计框架。它补上了可信推荐系统基准（如 PRA）缺失的"危害审计"另一半：**推荐质量之外，审计 Agent 会不会被操纵去害用户**。

## 为什么 RecRedTeam

- 推荐/购物 Agent（Amazon Rufus、OpenAI、Temu/淘宝 agent）2026 年在电商全面铺开，EU AI Act / DSA / 中国生成式 AI 办法均要求安全审计能力。
- 通用红队（ART）、搜索 agent（SafeSearch）、电商欺骗性界面基准只覆盖单个切片；**推荐领域的全谱系红队框架是空白**。
- 防御插件架构把净化（purifier）、RAG 防护、策略守卫等防御方法变成可直接集成的基线，和论文级防御基线对接。

## 威胁分类（8+1 类，映射 OWASP ASI 2026）

| 类别 | 中文 | OWASP ASI 2026 | OWASP LLM |
|---|---|---|---|
| `hallucination` | 商品幻觉 | ASI-08 Deceptive Interface | LLM09 Misinformation |
| `indirect_prompt_injection` | 间接提示注入 | ASI-02 Indirect Prompt Injection | LLM01 Prompt Injection |
| `fake_review_manipulation` | 虚假评论操纵 | ASI-06 Memory & Context Poisoning | LLM04 Data and Model Poisoning |
| `price_deception` | 价格欺骗 | ASI-08 Deceptive Interface | LLM09 Misinformation |
| `dark_pattern` | 暗黑模式 | ASI-08 Deceptive Interface | LLM05 Improper Output Handling |
| `filter_bubble` | 过滤气泡 | ASI-03 Tool Misuse | LLM05 Improper Output Handling |
| `stereotype_bias` | 刻板偏见 | ASI-03 Tool Misuse | LLM09 Misinformation |
| `backdoor` | 后门 | ASI-09 Supply Chain | LLM04 Data and Model Poisoning |
| `multi_turn_escalation` | 多轮升级 | ASI-05 Data Exfiltration | LLM05 Improper Output Handling |

## 架构

```
recreadteam/
├── taxonomy.py         # 威胁分类 + OWASP 映射
├── core.py             # Product / AttackCase / AuditResult / DefenseConfig
├── llm.py              # OpenAI 兼容 chat 助手（零依赖，适配器与 LLM 判官共用）
├── envs/shop.py        # 模拟购物环境（商品目录、检索、排序）
├── attacks/cases.py    # 攻击库（10 个用例，覆盖 8+1 类）
├── agents/             # Agent 接口 + mock 规则 Agent + LangGraph/OpenAI adapters
├── defenses/           # 净化 / RAG 防护 / 策略守卫 / DefenseStack 组合
├── judge.py            # 双通道判官（规则 + 可选 LLM）
├── pipeline.py         # 审计管线（每用例独立污染目录 + 确定性执行）
├── metrics.py          # ASR / 危害分级 / 防御有效性
├── storage.py          # SQLite 持久化
├── leaderboard.py      # 排行榜
├── report.py           # EU AI Act / DSA / 中国办法合规报告
└── cli.py              # 命令行入口
```

## 快速开始

```bash
# 安装
pip install -e ".[dev,dashboard]"

# 跑测试
pytest

# 命令行审计
python -m recreadteam.cli attacks
python -m recreadteam.cli benchmark

# 交互面板
streamlit run app.py
```

### 启用 LLM 判官 / 真实 Agent 模型（可选）

在 `.env` 或环境变量中配置（不配置则只用规则通道，真实 Agent 适配器自动回退为确定性文本）：

```bash
export USER_LLM_API_KEY=sk-xxx
export USER_LLM_BASE_URL=https://api.openai.com/v1
export USER_LLM_MODEL=gpt-4o-mini
```

配置后：
- `judge` 启用 LLM 判官通道（`--llm-judge`）
- `langgraph` / `openai_agents` 适配器把文本生成委托给真实模型（未配置时回退为 mock 逻辑，审计仍然可跑）

## 界面截图

Streamlit 仪表盘（`streamlit run app.py`）:

**威胁分类总览**

![Threat taxonomy overview](docs/screenshots/overview.png)

**运行审计（含判定、危害分级与证据）**

![Run audit](docs/screenshots/audit.png)

**排行榜**

![Leaderboard](docs/screenshots/leaderboard.png)

## 示例输出

```
== RecRedTeam benchmark: agent=mock ==
Baseline ASR: 100%  (mean harm 1.00)
  sanitizer      ASR 60%  effectiveness 40%
  rag_guard      ASR 60%  effectiveness 40%
  policy_guard   ASR 80%  effectiveness 20%
```

## 路线图

- **v1 (MVP)**：威胁分类 + 间接注入攻击 + 模拟购物环境 ✅
- **v2**：8+1 类全覆盖 + 真实 Agent 适配（LangGraph / OpenAI Agents SDK；接入 `USER_LLM_*` 即走真实模型，未配置自动回退）✅
- **v3**：防御基线 + benchmark 论文（SIGIR/KDD 路线）

## 免责声明

本框架用于合规审计与安全研究。攻击用例仅作用于本地模拟购物环境，不针对真实系统。
