"""RecRedTeam Streamlit dashboard.

Run with: streamlit run app.py
"""

from __future__ import annotations

import json
import os

import pandas as pd
import streamlit as st

from recreadteam.agents.mock import MockShoppingAgent
from recreadteam.attacks.cases import ALL_ATTACKS
from recreadteam.defenses import DEFENSE_REGISTRY, DefenseStack
from recreadteam.judge import Judge
from recreadteam.metrics import defense_effectiveness
from recreadteam.pipeline import AuditPipeline
from recreadteam.report import generate_compliance_report
from recreadteam.storage import Storage
from recreadteam.taxonomy import ALL_CATEGORIES

st.set_page_config(page_title="RecRedTeam", page_icon=":shield:", layout="wide")

DB_PATH = os.environ.get("RRT_DB", "recreadteam.db")


def make_agent_builder(agent_name: str):
    def _build(env, defense):
        if agent_name == "langgraph":
            from recreadteam.agents.langgraph_adapter import LangGraphShoppingAgent

            return LangGraphShoppingAgent(env, defense)
        if agent_name == "openai_agents":
            from recreadteam.agents.openai_adapter import OpenAIAgentsShoppingAgent

            return OpenAIAgentsShoppingAgent(env, defense)
        return MockShoppingAgent(env, defense)

    return _build


st.sidebar.title("RecRedTeam")
st.sidebar.caption("LLM/Agentic 推荐系统红队审计框架")

mode = st.sidebar.radio("导航", ["概览 / 威胁分类", "运行审计", "防御效果", "排行榜", "合规报告"])

# ---------------------------------------------------------------------------
if mode == "概览 / 威胁分类":
    st.title("RecRedTeam 威胁分类")
    st.markdown(
        "首个面向推荐/购物 Agent 的全谱系安全审计框架 —— 威胁分类 + 攻击库 + 审计管线 + 排行榜 + 防御插件。"
    )
    st.markdown("**映射到 OWASP ASI 2026 / LLM Top-10**")
    rows = []
    for cat in ALL_CATEGORIES:
        rows.append(
            {
                "类别 ID": cat.id,
                "名称": cat.name,
                "中文": cat.name_cn,
                "OWASP ASI 2026": cat.owasp_asi,
                "OWASP LLM": cat.owasp_llm,
                "默认危害": cat.default_severity,
                "描述": cat.description,
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
elif mode == "运行审计":
    st.title("运行审计")

    agent_name = st.selectbox("Agent", ["mock", "langgraph", "openai_agents"])
    defense_ids = st.multiselect(
        "防御插件",
        list(DEFENSE_REGISTRY),
        default=[],
        help="sanitizer=输入净化; rag_guard=检索防护; policy_guard=输出策略守卫",
    )
    llm_judge = st.checkbox("启用 LLM 判官（需配置 USER_LLM_* 环境变量）", value=False)

    st.markdown("### 攻击用例")
    selected = {
        a.attack_id: st.checkbox(f"{a.attack_id} - {a.name}", value=True)
        for a in ALL_ATTACKS
    }
    chosen_attacks = [a for a in ALL_ATTACKS if selected[a.attack_id]]

    if st.button("运行审计"):
        if not chosen_attacks:
            st.warning("至少选择一个攻击用例")
        else:
            defense = None
            if defense_ids:
                defense = DefenseStack([DEFENSE_REGISTRY[d]() for d in defense_ids])

            with st.spinner("审计中..."):
                storage = Storage(DB_PATH)
                pipeline = AuditPipeline(judge=Judge(use_llm=llm_judge), storage=storage)
                report = pipeline.run_suite(
                    attacks=chosen_attacks,
                    agent_builder=make_agent_builder(agent_name),
                    defense=defense,
                    agent_id=agent_name,
                )
                storage.close()

            st.session_state["last_report"] = report.to_dict()
            st.success(f"审计完成: run_id={report.run_id}")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("ASR", f"{report.summary['asr']:.0%}")
            c2.metric("平均危害分", f"{report.summary['mean_score']:.2f}")
            c3.metric("成功攻击", f"{report.summary['success']}/{report.summary['total']}")
            c4.metric("危害分布", json.dumps(report.summary["hazards"], ensure_ascii=False))

            rows = [
                {
                    "攻击 ID": r.attack_id,
                    "攻击名": r.attack_name,
                    "类别": r.category_id,
                    "判定": r.verdict,
                    "危害": r.hazard,
                    "得分": r.score,
                    "证据": "; ".join(r.evidence),
                    "响应": r.response[:200],
                }
                for r in report.results
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
elif mode == "防御效果":
    st.title("防御效果对比")
    agent_name = st.selectbox("Agent", ["mock", "langgraph", "openai_agents"], key="eff_agent")
    if st.button("运行对比基准"):
        with st.spinner("运行 baseline + 各防御..."):
            storage = Storage(DB_PATH)
            pipeline = AuditPipeline(judge=Judge(use_llm=False), storage=storage)
            reports = pipeline.run_benchmark(
                make_agent_builder(agent_name),
                defenses=[DEFENSE_REGISTRY[d]() for d in DEFENSE_REGISTRY],
                agent_id=agent_name,
            )
            storage.close()

        baseline = reports[0]
        rows = []
        for r in reports[1:]:
            eff = defense_effectiveness(baseline.summary["asr"], r.summary["asr"])
            rows.append(
                {
                    "防御": r.defense_ids[0] if r.defense_ids else "none",
                    "ASR": f"{r.summary['asr']:.0%}",
                    "平均危害": f"{r.summary['mean_score']:.2f}",
                    "防御有效性": f"{eff:.0%}",
                }
            )
        st.markdown(f"**Baseline ASR: {baseline.summary['asr']:.0%}**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        chart_df = pd.DataFrame(
            {
                "防御": [r["防御"] for r in rows],
                "ASR (%)": [float(r["ASR"].rstrip("%")) for r in rows],
            }
        ).set_index("防御")
        st.bar_chart(chart_df)

# ---------------------------------------------------------------------------
elif mode == "排行榜":
    st.title("排行榜")
    storage = Storage(DB_PATH)
    rows = storage.leaderboard()
    storage.close()
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("暂无数据，请先运行审计或对比基准。")

# ---------------------------------------------------------------------------
elif mode == "合规报告":
    st.title("合规报告 (EU AI Act / DSA / 中国生成式AI办法 / OWASP)")
    st.caption("基于最近一次审计结果生成。")
    report_data = st.session_state.get("last_report")
    if report_data is None:
        storage = Storage(DB_PATH)
        results = storage.all_results()
        storage.close()
    else:
        from recreadteam.core import AuditResult

        results = [AuditResult(**{**r, "defense_ids": tuple(r.get("defense_ids", []))}) for r in report_data["results"]]

    if results:
        text = generate_compliance_report(results)
        st.markdown(text)
        st.download_button("下载 Markdown", text, file_name="recrredteam_report.md")
    else:
        st.info("暂无审计结果。")
