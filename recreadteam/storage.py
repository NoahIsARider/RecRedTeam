"""SQLite storage for audit runs and leaderboard snapshots."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Optional

from .core import AuditResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    attack_id TEXT NOT NULL,
    attack_name TEXT,
    category_id TEXT,
    agent_id TEXT,
    defense_ids TEXT,
    user_query TEXT,
    response TEXT,
    verdict TEXT,
    hazard TEXT,
    score REAL,
    evidence TEXT,
    llm_reason TEXT,
    meta TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS leaderboard (
    key TEXT PRIMARY KEY,
    agent_id TEXT,
    defense_ids TEXT,
    asr REAL,
    mean_score REAL,
    hazard_hist TEXT,
    updated_at TEXT
);
"""


class Storage:
    def __init__(self, db_path: str | Path = "recreadteam.db"):
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def save_result(self, result: AuditResult, run_id: str) -> str:
        row_id = str(uuid.uuid4())
        self._conn.execute(
            """INSERT INTO audit_results
               (id, run_id, attack_id, attack_name, category_id, agent_id,
                defense_ids, user_query, response, verdict, hazard, score,
                evidence, llm_reason, meta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row_id,
                run_id,
                result.attack_id,
                result.attack_name,
                result.category_id,
                result.agent_id,
                json.dumps(list(result.defense_ids)),
                result.user_query,
                result.response,
                result.verdict,
                result.hazard,
                result.score,
                json.dumps(result.evidence),
                result.llm_reason,
                json.dumps(result.meta),
            ),
        )
        self._conn.commit()
        return row_id

    def results_for_run(self, run_id: str) -> list[AuditResult]:
        rows = self._conn.execute(
            "SELECT * FROM audit_results WHERE run_id = ?", (run_id,)
        ).fetchall()
        return [self._row_to_result(r) for r in rows]

    def all_results(self, limit: int = 1000) -> list[AuditResult]:
        rows = self._conn.execute(
            "SELECT * FROM audit_results ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_result(r) for r in rows]

    def upsert_leaderboard(
        self,
        agent_id: str,
        defense_ids: tuple[str, ...],
        asr: float,
        mean_score: float,
        hazard_hist: dict[str, int],
    ) -> None:
        key = f"{agent_id}|{','.join(defense_ids)}"
        self._conn.execute(
            """INSERT INTO leaderboard (key, agent_id, defense_ids, asr, mean_score, hazard_hist, updated_at)
               VALUES (?,?,?,?,?,?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET
                 asr=excluded.asr, mean_score=excluded.mean_score,
                 hazard_hist=excluded.hazard_hist, updated_at=excluded.updated_at""",
            (
                key,
                agent_id,
                json.dumps(list(defense_ids)),
                asr,
                mean_score,
                json.dumps(hazard_hist),
            ),
        )
        self._conn.commit()

    def leaderboard(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM leaderboard ORDER BY asr DESC, mean_score DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_result(row) -> AuditResult:
        return AuditResult(
            attack_id=row["attack_id"],
            attack_name=row["attack_name"] or "",
            category_id=row["category_id"] or "",
            agent_id=row["agent_id"] or "",
            defense_ids=tuple(json.loads(row["defense_ids"] or "[]")),
            user_query=row["user_query"] or "",
            response=row["response"] or "",
            verdict=row["verdict"] or "",
            hazard=row["hazard"] or "",
            score=float(row["score"] or 0.0),
            evidence=json.loads(row["evidence"] or "[]"),
            llm_reason=row["llm_reason"] or "",
            meta=json.loads(row["meta"] or "{}"),
        )
