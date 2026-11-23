"""Reliable Redis queue: at-least-once delivery, retries with backoff, dead letters.

pending -> BLMOVE -> processing:<worker> -> ack (LREM)
                                         -> fail -> delayed (zset) -> pending
                                                 -> dead after MAX_ATTEMPTS
A worker whose heartbeat expires gets its processing list pushed back to pending.
"""

import json
import time
import uuid

import redis

MAX_ATTEMPTS = 3
HEARTBEAT_TTL = 30


def dumps(job: dict) -> str:
    # LREM/ZREM match on the exact string, so serialisation has to be stable
    return json.dumps(job, sort_keys=True)


class JobQueue:
    def __init__(self, r: redis.Redis, name: str = "ingest"):
        self.r = r
        self.p = f"q:{name}"

    def _processing(self, worker: str) -> str:
        return f"{self.p}:processing:{worker}"

    # producer

    def enqueue(self, payload: dict) -> str:
        job = {"id": uuid.uuid4().hex, "attempts": 0, "enqueued_at": time.time(), **payload}
        self.r.lpush(f"{self.p}:pending", dumps(job))
        return job["id"]

    # worker side

    def register(self, worker: str) -> None:
        self.r.sadd(f"{self.p}:workers", worker)
        self.heartbeat(worker)

    def heartbeat(self, worker: str) -> None:
        self.r.set(f"{self.p}:heartbeat:{worker}", time.time(), ex=HEARTBEAT_TTL)

    def reserve(self, worker: str, timeout: int = 5) -> str | None:
        return self.r.blmove(
            f"{self.p}:pending", self._processing(worker), timeout, src="RIGHT", dest="LEFT"
        )

    def ack(self, worker: str, raw: str) -> None:
        self.r.lrem(self._processing(worker), 1, raw)

    def fail(self, worker: str, raw: str, error: Exception) -> str:
        job = json.loads(raw)
        job["attempts"] += 1
        job["last_error"] = f"{type(error).__name__}: {error}"[:500]

        pipe = self.r.pipeline(transaction=True)
        pipe.lrem(self._processing(worker), 1, raw)
        if job["attempts"] >= MAX_ATTEMPTS:
            pipe.lpush(f"{self.p}:dead", dumps(job))
            outcome = "dead"
        else:
            delay = 2 ** job["attempts"] * 5  # 10s, then 20s
            pipe.zadd(f"{self.p}:delayed", {dumps(job): time.time() + delay})
            outcome = f"retry in {delay}s"
        pipe.execute()
        return outcome

    # housekeeping, every worker runs these; safe to run concurrently

    def promote_delayed(self) -> int:
        moved = 0
        due = self.r.zrangebyscore(f"{self.p}:delayed", 0, time.time(), start=0, num=100)
        for raw in due:
            # only one worker gets 1 back from ZREM, so the job moves once
            if self.r.zrem(f"{self.p}:delayed", raw):
                self.r.lpush(f"{self.p}:pending", raw)
                moved += 1
        return moved

    def reap_dead_workers(self) -> int:
        moved = 0
        for worker in self.r.smembers(f"{self.p}:workers"):
            if self.r.exists(f"{self.p}:heartbeat:{worker}"):
                continue
            while self.r.lmove(self._processing(worker), f"{self.p}:pending", "RIGHT", "LEFT"):
                moved += 1
            self.r.srem(f"{self.p}:workers", worker)
        return moved

    def requeue_dead(self) -> int:
        n = 0
        while raw := self.r.rpop(f"{self.p}:dead"):
            job = json.loads(raw)
            job["attempts"] = 0
            job.pop("last_error", None)
            self.r.lpush(f"{self.p}:pending", dumps(job))
            n += 1
        return n

    def dead_jobs(self, limit: int = 50) -> list[dict]:
        return [json.loads(raw) for raw in self.r.lrange(f"{self.p}:dead", 0, limit - 1)]

    def stats(self) -> dict:
        return {
            "pending": self.r.llen(f"{self.p}:pending"),
            "delayed": self.r.zcard(f"{self.p}:delayed"),
            "dead": self.r.llen(f"{self.p}:dead"),
            "workers": self.r.scard(f"{self.p}:workers"),
        }


def connect(url: str) -> JobQueue:
    return JobQueue(redis.Redis.from_url(url, decode_responses=True))
