import json
import logging
import os
import signal
import socket
import sys
import threading
import time

from .config import settings
from .db import open_pool, pool
from .jobqueue import JobQueue, connect

log = logging.getLogger("worker")
stopping = threading.Event()


def worker_id() -> str:
    if wid := os.environ.get("WORKER_ID"):
        return wid
    # Cloud Run Jobs give every task an index
    if (task := os.environ.get("CLOUD_RUN_TASK_INDEX")) is not None:
        return f"{os.environ.get('CLOUD_RUN_EXECUTION', 'job')}-{task}"
    return f"{socket.gethostname()}-{os.getpid()}"


def _housekeeping(q: JobQueue, worker: str) -> None:
    # Separate thread so a 200-page textbook that takes two minutes
    # doesn't make this worker look dead.
    while not stopping.wait(10):
        try:
            q.heartbeat(worker)
            q.promote_delayed()
            if n := q.reap_dead_workers():
                log.warning("reaped %d job(s) from dead workers", n)
        except Exception:  # noqa: BLE001
            log.exception("housekeeping failed, will retry")


def load_classifier():
    if not os.path.exists(settings.classifier_path):
        return None
    from .classifier.predict import TopicClassifier

    return TopicClassifier.load(settings.classifier_path)


def main(drain: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    worker = worker_id()
    signal.signal(signal.SIGTERM, lambda *_: stopping.set())
    signal.signal(signal.SIGINT, lambda *_: stopping.set())

    open_pool()
    q = connect(settings.redis_url)
    q.register(worker)
    threading.Thread(target=_housekeeping, args=(q, worker), daemon=True).start()

    from .ingest.embedder import Embedder
    from .ingest.pipeline import process_document

    embedder = Embedder(settings.embed_model)
    classifier = load_classifier()

    log.info("worker %s ready (classifier: %s)", worker, "yes" if classifier else "no")
    # stop is only checked between jobs: on SIGTERM we finish the current document first
    while not stopping.is_set():
        raw = q.reserve(worker, timeout=5)
        if raw is None:
            if drain:
                s = q.stats()
                if s["pending"] == 0 and s["delayed"] == 0:
                    break
            continue

        job = json.loads(raw)
        started = time.perf_counter()
        try:
            n = process_document(job, embedder, classifier)
            q.ack(worker, raw)
            log.info("job %s done: %d chunks in %.1fs", job["id"], n, time.perf_counter() - started)
        except Exception as e:  # noqa: BLE001
            outcome = q.fail(worker, raw, e)
            log.exception("job %s failed (%s)", job["id"], outcome)
            if outcome == "dead":
                with pool.connection() as conn:
                    conn.execute(
                        "UPDATE documents SET status = 'failed', error = %s, updated_at = now() "
                        "WHERE id = %s",
                        (str(e)[:500], job["document_id"]),
                    )

    stopping.set()
    log.info("worker %s stopped", worker)


if __name__ == "__main__":
    main(drain="--drain" in sys.argv)
