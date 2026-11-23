from psycopg.rows import dict_row

from .db import pool

WEAKEST_SQL = """
WITH recent AS (
  SELECT q.topic_id,
         a.score::real / a.max_score                                   AS frac,
         exp(-extract(epoch FROM now() - a.answered_at) / 86400.0 / 7) AS w
  FROM quiz_attempts a
  JOIN quiz_questions q ON q.id = a.question_id
  WHERE a.answered_at > now() - interval '30 days'
),
per_topic AS (
  SELECT t.id, t.name, t.course_id, t.exam_weight,
         count(r.topic_id)                       AS attempts,
         sum(r.w * r.frac) / nullif(sum(r.w), 0) AS mastery
  FROM topics t
  LEFT JOIN recent r ON r.topic_id = t.id
  WHERE %(course)s::text IS NULL OR t.course_id = %(course)s
  GROUP BY t.id
)
SELECT id, name, course_id, attempts,
       round(coalesce(mastery, 0)::numeric, 2)                       AS mastery,
       round((exam_weight * (1 - coalesce(mastery, 0)))::numeric, 2) AS priority
FROM per_topic
ORDER BY priority DESC, attempts ASC
LIMIT %(limit)s
"""

MISTAKES_SQL = """
SELECT q.topic_id, q.question, q.answer AS reference_answer,
       a.user_answer, a.score, a.max_score, a.feedback, a.answered_at
FROM quiz_attempts a
JOIN quiz_questions q ON q.id = a.question_id
JOIN topics t ON t.id = q.topic_id
WHERE a.score < a.max_score
  AND (%(course)s::text IS NULL OR t.course_id = %(course)s)
ORDER BY a.answered_at DESC
LIMIT %(limit)s
"""

DAILY_SQL = """
SELECT d::date AS day,
       count(a.id)                                         AS answered,
       round(avg(a.score::real / a.max_score)::numeric, 2) AS accuracy
FROM generate_series(now()::date - 13, now()::date, interval '1 day') d
LEFT JOIN quiz_attempts a ON a.answered_at::date = d::date
GROUP BY d
ORDER BY d
"""

FIRST_TRY_SQL = """
SELECT q.topic_id,
       round(avg(first.score::real / first.max_score)::numeric, 2) AS first_try_accuracy,
       count(*) AS questions
FROM (
  SELECT a.*, row_number() OVER (PARTITION BY a.question_id ORDER BY a.answered_at) AS rn
  FROM quiz_attempts a
) first
JOIN quiz_questions q ON q.id = first.question_id
WHERE first.rn = 1
GROUP BY q.topic_id
ORDER BY first_try_accuracy
"""

SPEND_SQL = """
SELECT kind,
       count(*)                AS calls,
       round(sum(cost_usd), 4) AS usd,
       round(avg(latency_ms))  AS avg_ms,
       round(sum(cache_read_tokens)::numeric
             / nullif(sum(input_tokens + cache_read_tokens + cache_write_tokens), 0), 2) AS cache_hit
FROM llm_calls
WHERE created_at > now() - interval '7 days'
GROUP BY kind
ORDER BY usd DESC
"""

DOCUMENTS_SQL = """
SELECT d.id, d.filename, d.course_id, d.status, d.pages, d.error, d.updated_at,
       count(c.id) AS chunks
FROM documents d
LEFT JOIN chunks c ON c.document_id = d.id
GROUP BY d.id
ORDER BY d.created_at DESC
"""

MASTERY_SQL = WEAKEST_SQL.replace(
    "ORDER BY priority DESC, attempts ASC", "ORDER BY course_id, id"
)


def _rows(sql: str, params: dict | None = None) -> list[dict]:
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(sql, params or {}).fetchall()


def weakest_topics(course: str | None = None, limit: int = 5) -> list[dict]:
    return _rows(WEAKEST_SQL, {"course": course, "limit": limit})


def mastery_by_topic(course: str | None = None) -> list[dict]:
    return _rows(MASTERY_SQL, {"course": course, "limit": 1000})


def recent_mistakes(course: str | None = None, limit: int = 8) -> list[dict]:
    return _rows(MISTAKES_SQL, {"course": course, "limit": limit})


def accuracy_by_day() -> list[dict]:
    return _rows(DAILY_SQL)


def first_try_accuracy() -> list[dict]:
    return _rows(FIRST_TRY_SQL)


def spend_by_kind() -> list[dict]:
    return _rows(SPEND_SQL)


def documents() -> list[dict]:
    return _rows(DOCUMENTS_SQL)


def chunk_counts() -> list[dict]:
    return _rows("SELECT course_id, count(*) AS chunks FROM chunks GROUP BY course_id ORDER BY 1")
