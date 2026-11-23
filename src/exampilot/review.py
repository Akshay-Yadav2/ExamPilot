"""Spaced repetition, a cut-down SM-2. One exam-specific tweak: nothing gets
scheduled after the exam, the interval is capped at half the days left."""

import heapq
from datetime import date, datetime, timedelta

from psycopg.rows import dict_row


def next_interval(interval: float, ease: float, reps: int, frac: float) -> tuple[float, float, int]:
    if frac < 0.5:
        return 1.0, max(1.3, ease - 0.2), 0  # wrong: start over, a bit harder
    reps += 1
    if reps == 1:
        interval = 1.0
    elif reps == 2:
        interval = 3.0
    else:
        interval *= ease
    ease += 0.1 if frac == 1.0 else -0.05
    return interval, ease, reps


def cap_for_exam(interval: float, now: datetime, exam_date: date | None) -> float:
    if exam_date is None:
        return interval
    days_left = (exam_date - now.date()).days
    return min(interval, max(0.5, days_left / 2))


def schedule(conn, question_id: str, frac: float, now: datetime,
             exam_date: date | None = None) -> None:
    row = conn.execute(
        "SELECT interval_days, ease, reps FROM reviews WHERE question_id = %s FOR UPDATE",
        (question_id,),
    ).fetchone()
    interval, ease, reps = row if row else (0.0, 2.5, 0)
    interval, ease, reps = next_interval(interval, ease, reps, frac)
    interval = cap_for_exam(interval, now, exam_date)
    conn.execute(
        "INSERT INTO reviews (question_id, due_at, interval_days, ease, reps) "
        "VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (question_id) DO UPDATE SET due_at = EXCLUDED.due_at, "
        "interval_days = EXCLUDED.interval_days, ease = EXCLUDED.ease, reps = EXCLUDED.reps",
        (question_id, now + timedelta(days=interval), interval, ease, reps),
    )


def next_due(conn, course: str, now: datetime) -> dict | None:
    # The API runs several replicas, so the "heap" here is the due_at index.
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "SELECT q.id, q.topic_id, q.kind, q.question, q.choices, q.answer, q.explanation, "
            "       q.source_chunk_ids, r.due_at, t.name AS topic_name, "
            "       (SELECT max(answered_at) FROM quiz_attempts a WHERE a.question_id = q.id) "
            "         AS last_seen "
            "FROM reviews r "
            "JOIN quiz_questions q ON q.id = r.question_id "
            "JOIN topics t ON t.id = q.topic_id "
            "WHERE t.course_id = %s AND r.due_at <= %s "
            "ORDER BY r.due_at LIMIT 1",
            (course, now),
        ).fetchone()


class ReviewQueue:
    """In-memory min-heap of (due, question_id) with lazy deletion.

    Used by the terminal quiz and the simulator where one process owns the state.
    Rescheduling just pushes again; the stale entry is skipped when it surfaces.
    """

    def __init__(self) -> None:
        self._heap: list[tuple[datetime, str]] = []
        self._due: dict[str, datetime] = {}

    def push(self, question_id: str, due: datetime) -> None:
        self._due[question_id] = due
        heapq.heappush(self._heap, (due, question_id))

    def pop_due(self, now: datetime) -> str | None:
        while self._heap:
            due, qid = self._heap[0]
            if self._due.get(qid) != due:
                heapq.heappop(self._heap)
                continue
            if due > now:
                return None
            heapq.heappop(self._heap)
            del self._due[qid]
            return qid
        return None

    def __len__(self) -> int:
        return len(self._due)
