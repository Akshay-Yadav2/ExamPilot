"""Fill a fresh database with two weeks of made-up quiz history.

Lets you click around the Quiz and Progress pages without spending API credits.
Ingest the sample notes first so questions can point at real chunks:

    python -m exampilot.cli ingest samples/daa --course daa --inline   (same for swe, ai)
    python -m exampilot.cli seed
    python -m exampilot.cli seed --clear

Everything it writes is tagged model = 'sample' so --clear can find it again.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
from psycopg.types.json import Jsonb

from . import bandit, review
from .db import pool
from .llm import PRICES

log = logging.getLogger(__name__)

TAG = "sample"
DEFAULT_FILE = Path(__file__).resolve().parents[2] / "samples" / "quiz.json"

# How good the pretend student is at each topic on day one. Anything not listed
# starts at 0.6. Picked so the weakest-topics list has something to say.
START_SKILL = {
    "daa.dp": 0.25,
    "daa.flow": 0.35,
    "daa.np": 0.45,
    "ai.mdp_rl": 0.3,
    "ai.probability": 0.5,
    "swe.patterns": 0.4,
    "swe.process": 0.85,
    "daa.greedy": 0.75,
    "swe.uml": 0.5,
    "ai.logic": 0.45,
}

FEEDBACK = {
    2: "Covers the key idea and explains why. Good.",
    1: "Right direction, but one of the essential points is missing.",
    0: "This misses the main idea. Compare with the reference answer.",
}


def _source_chunks(cur, course: str, query: str) -> list[str]:
    rows = cur.execute(
        "SELECT c.id FROM chunks c, websearch_to_tsquery('english', %s) q "
        "WHERE c.course_id = %s AND c.tsv @@ q "
        "ORDER BY ts_rank_cd(c.tsv, q) DESC LIMIT 2",
        (query.replace(" ", " or "), course),
    ).fetchall()
    return [r[0] for r in rows]


def _cost(inp: int, out: int, cache_read: int = 0, cache_write: int = 0) -> float:
    p = PRICES["claude-opus-5-5"]
    return (inp * p["input"] + out * p["output"] + cache_read * p["cache_read"]
            + cache_write * p["cache_write"]) / 1_000_000


def already_seeded() -> bool:
    with pool.connection() as conn:
        return conn.execute(
            "SELECT EXISTS (SELECT 1 FROM quiz_questions WHERE model = %s)", (TAG,)
        ).fetchone()[0]


def seed(path: Path = DEFAULT_FILE, days: int = 14, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    questions = json.loads(Path(path).read_text())
    now = datetime.now(UTC)

    # 1. questions, each pointing at the chunks that best match its keywords
    inserted, no_source = [], 0
    with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        courses = dict(cur.execute("SELECT id, course_id FROM topics").fetchall())
        exam_dates = dict(cur.execute("SELECT id, exam_date FROM courses").fetchall())
        for q in questions:
            if q["topic_id"] not in courses:
                raise ValueError(f"unknown topic {q['topic_id']}, load db/topics.sql first")
            course = courses[q["topic_id"]]
            ids = _source_chunks(cur, course, q["source"])
            no_source += not ids
            qid = cur.execute(
                "INSERT INTO quiz_questions (topic_id, kind, question, choices, answer, "
                "explanation, source_chunk_ids, model, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (q["topic_id"], q["kind"], q["question"], Jsonb(q["choices"]), q["answer"],
                 q["explanation"], ids, TAG, now - timedelta(days=days + 1)),
            ).fetchone()[0]
            inserted.append({**q, "id": qid, "course": course})

    # 2. every topic gets practised, but where a topic has more than one question,
    #    leave some unanswered so the quiz still has fresh ones to serve offline
    by_topic: dict[str, list[dict]] = {}
    for i in rng.permutation(len(inserted)):
        by_topic.setdefault(inserted[i]["topic_id"], []).append(inserted[i])
    answered = {t: qs[:1] + [q for q in qs[1:] if rng.random() < 0.4]
                for t, qs in by_topic.items()}
    topic_ids = sorted(answered)
    skill = {t: START_SKILL.get(t, 0.6) for t in topic_ids}

    # 3. replay attempts day by day, oldest first, through the real update code
    attempts = calls = 0
    with pool.connection() as conn, conn.transaction():
        for day in range(days, -1, -1):
            if rng.random() < 0.15:  # skipped days happen
                continue
            hours_ago = sorted(rng.uniform(0.5, 10, int(rng.integers(7, 15))), reverse=True)
            for h in hours_ago:  # oldest first
                pool_ = answered[topic_ids[int(rng.integers(len(topic_ids)))]]
                q = pool_[int(rng.integers(len(pool_)))]
                ts = now - timedelta(days=day, hours=float(h))
                p = skill[q["topic_id"]]
                if q["kind"] == "mcq":
                    score = 2 if rng.random() < p else 0
                    feedback, answer = q["explanation"], q["answer"] if score else q["choices"][-1]
                else:
                    score = int(rng.choice([0, 1, 2], p=[(1 - p) ** 2, 2 * p * (1 - p), p**2]))
                    feedback, answer = FEEDBACK[score], "(sample answer)"
                    _fake_call(conn, "grade", ts, rng)
                    calls += 1
                skill[q["topic_id"]] = min(0.95, p + 0.04 * (1 - p))  # practice helps a bit

                conn.execute(
                    "INSERT INTO quiz_attempts (question_id, user_answer, score, max_score, "
                    "feedback, answered_at) VALUES (%s, %s, %s, 2, %s, %s)",
                    (q["id"], answer, score, feedback, ts),
                )
                alpha, beta, updated = conn.execute(
                    "SELECT alpha, beta, updated_at FROM topic_stats WHERE topic_id = %s "
                    "FOR UPDATE", (q["topic_id"],),
                ).fetchone()
                alpha, beta = bandit.update(alpha, beta, min(updated, ts), score / 2, ts)
                conn.execute(
                    "UPDATE topic_stats SET alpha = %s, beta = %s, updated_at = %s "
                    "WHERE topic_id = %s", (alpha, beta, ts, q["topic_id"]),
                )
                review.schedule(conn, q["id"], score / 2, ts, exam_dates.get(q["course"]))
                attempts += 1

            for _ in range(int(rng.integers(2, 7))):
                _fake_call(conn, "chat", now - timedelta(days=day, hours=float(rng.uniform(0, 12))), rng)
                calls += 1
            if day % 4 == 0:
                _fake_call(conn, "quiz_gen", now - timedelta(days=day, hours=1), rng)
                calls += 1

    if no_source:
        log.warning("%d questions found no matching chunk; ingest samples/ first", no_source)
    return {"questions": len(inserted), "attempts": attempts, "llm_calls": calls,
            "without_sources": no_source}


def _fake_call(conn, kind: str, ts: datetime, rng: np.random.Generator) -> None:
    if kind == "chat":
        cached = rng.random() < 0.75  # follow-up turns mostly hit the cache
        inp = int(rng.integers(900, 2500)) if cached else int(rng.integers(6000, 11000))
        read = int(rng.integers(6000, 9000)) if cached else 0
        write = 0 if cached else int(rng.integers(4000, 6000))
        out, ms = int(rng.integers(400, 1200)), int(rng.integers(3500, 9000))
    elif kind == "grade":
        inp, read, write = int(rng.integers(1200, 1800)), 0, 0
        out, ms = int(rng.integers(250, 500)), int(rng.integers(2500, 6000))
    else:
        inp, read, write = int(rng.integers(3500, 4500)), 0, 0
        out, ms = int(rng.integers(1600, 2400)), int(rng.integers(12000, 22000))
    conn.execute(
        "INSERT INTO llm_calls (kind, model, input_tokens, output_tokens, cache_read_tokens, "
        "cache_write_tokens, latency_ms, cost_usd, stop_reason, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'end_turn', %s)",
        (kind, TAG, inp, out, read, write, ms, _cost(inp, out, read, write), ts),
    )


def clear() -> dict:
    """Remove everything seed() wrote and reset the scheduler state it touched."""
    with pool.connection() as conn, conn.transaction():
        topics = [r[0] for r in conn.execute(
            "SELECT DISTINCT topic_id FROM quiz_questions WHERE model = %s", (TAG,))]
        sample_q = "SELECT id FROM quiz_questions WHERE model = %s"
        a = conn.execute(f"DELETE FROM quiz_attempts WHERE question_id IN ({sample_q})",
                         (TAG,)).rowcount
        conn.execute(f"DELETE FROM reviews WHERE question_id IN ({sample_q})", (TAG,))
        q = conn.execute("DELETE FROM quiz_questions WHERE model = %s", (TAG,)).rowcount
        c = conn.execute("DELETE FROM llm_calls WHERE model = %s", (TAG,)).rowcount
        conn.execute("UPDATE topic_stats SET alpha = 1, beta = 1, updated_at = now() "
                     "WHERE topic_id = ANY(%s)", (topics,))
    return {"questions": q, "attempts": a, "llm_calls": c}
