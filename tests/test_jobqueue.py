import json
import threading
import time

import pytest

from exampilot import jobqueue
from exampilot.jobqueue import JobQueue

pytestmark = pytest.mark.redis


def test_enqueue_reserve_ack(redis_client):
    q = JobQueue(redis_client, "t")
    q.enqueue({"document_id": "d1"})
    raw = q.reserve("w1", timeout=1)
    assert json.loads(raw)["document_id"] == "d1"
    assert redis_client.llen("q:t:processing:w1") == 1
    q.ack("w1", raw)
    assert redis_client.llen("q:t:processing:w1") == 0
    assert q.stats()["pending"] == 0


def test_fifo(redis_client):
    q = JobQueue(redis_client, "t")
    for i in range(3):
        q.enqueue({"document_id": str(i)})
    got = [json.loads(q.reserve("w", 1))["document_id"] for _ in range(3)]
    assert got == ["0", "1", "2"]


def test_retry_then_dead(redis_client, monkeypatch):
    q = JobQueue(redis_client, "t")
    q.enqueue({"document_id": "d"})
    for attempt in range(1, jobqueue.MAX_ATTEMPTS + 1):
        raw = q.reserve("w", 1)
        assert raw, f"attempt {attempt} got nothing"
        outcome = q.fail("w", raw, ValueError("bad pdf"))
        if attempt < jobqueue.MAX_ATTEMPTS:
            assert outcome.startswith("retry")
            # pretend the backoff has passed
            monkeypatch.setattr(time, "time", lambda: 10**12)
            assert q.promote_delayed() == 1
            monkeypatch.undo()
    assert outcome == "dead"
    (dead,) = q.dead_jobs()
    assert dead["attempts"] == jobqueue.MAX_ATTEMPTS
    assert "bad pdf" in dead["last_error"]


def test_reaper_returns_dead_workers_job(redis_client):
    q = JobQueue(redis_client, "t")
    q.register("doomed")
    q.enqueue({"document_id": "d"})
    assert q.reserve("doomed", 1)
    redis_client.delete("q:t:heartbeat:doomed")  # as if the TTL ran out
    assert q.reap_dead_workers() == 1
    assert q.stats()["pending"] == 1
    assert q.stats()["workers"] == 0


def test_reaper_leaves_live_workers_alone(redis_client):
    q = JobQueue(redis_client, "t")
    q.register("alive")
    q.enqueue({"document_id": "d"})
    q.reserve("alive", 1)
    assert q.reap_dead_workers() == 0


def test_promote_runs_once_under_contention(redis_client):
    q = JobQueue(redis_client, "t")
    for i in range(50):
        redis_client.zadd("q:t:delayed", {jobqueue.dumps({"id": str(i)}): 0})
    moved = []
    threads = [threading.Thread(target=lambda: moved.append(q.promote_delayed()))
               for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(moved) == 50
    assert q.stats()["pending"] == 50


def test_requeue_dead(redis_client):
    q = JobQueue(redis_client, "t")
    redis_client.lpush("q:t:dead", jobqueue.dumps({"id": "1", "attempts": 3, "last_error": "x"}))
    assert q.requeue_dead() == 1
    job = json.loads(q.reserve("w", 1))
    assert job["attempts"] == 0 and "last_error" not in job
