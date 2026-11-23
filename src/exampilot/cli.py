"""Command line entry point.

    python -m exampilot.cli ingest ~/Desktop/"Sem 1"/"Design & Analysis Algorithms" --course daa
    python -m exampilot.cli ask "why does Dijkstra fail with negative edges?"
    python -m exampilot.cli chat
    python -m exampilot.cli quiz daa
    python -m exampilot.cli requeue-stuck
    python -m exampilot.cli seed            # sample quiz history, see samples/README.md
    python -m exampilot.cli status
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .config import COURSES, settings

SUFFIXES = {".pdf", ".md"}


def _register(path: Path, course: str) -> tuple[str, bool]:
    """Hash, store and insert a documents row. Returns (doc_id, is_new)."""
    from . import storage
    from .db import pool

    data = path.read_bytes()
    doc_id = hashlib.sha256(data).hexdigest()
    stored = storage.save(f"{doc_id}{path.suffix.lower()}", data)
    with pool.connection() as conn:
        row = conn.execute(
            "INSERT INTO documents (id, course_id, filename, path) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING RETURNING id",
            (doc_id, course, path.name, stored),
        ).fetchone()
    return doc_id, row is not None


def cmd_ingest(args) -> None:
    from .db import open_pool

    open_pool()
    root = Path(args.folder).expanduser()
    files = [root] if root.is_file() else sorted(
        p for p in root.rglob("*") if p.suffix.lower() in SUFFIXES and not p.name.startswith(".")
    )
    if not files:
        sys.exit(f"no .pdf or .md files under {root}")

    if args.inline:
        from .ingest.embedder import Embedder
        from .ingest.pipeline import process_document
        from .worker import load_classifier

        embedder, classifier = Embedder(settings.embed_model), load_classifier()
    else:
        from .jobqueue import connect

        q = connect(settings.redis_url)

    new = 0
    for path in files:
        doc_id, is_new = _register(path, args.course)
        new += is_new
        if args.inline:
            n = process_document({"document_id": doc_id}, embedder, classifier)
            print(f"  {path.name}: {n} chunks" if n else f"  {path.name}: already done")
        elif is_new:
            q.enqueue({"document_id": doc_id})
            print(f"  queued {path.name}")
        else:
            print(f"  skip {path.name} (already uploaded)")
    print(f"{len(files)} files, {new} new")


def cmd_requeue_stuck(args) -> None:
    """Docs stuck in 'queued' (API died between insert and enqueue). Safe: ingest is idempotent."""
    from .db import open_pool, pool
    from .jobqueue import connect

    open_pool()
    q = connect(settings.redis_url)
    cutoff = datetime.now(UTC) - timedelta(minutes=args.minutes)
    with pool.connection() as conn:
        ids = [r[0] for r in conn.execute(
            "SELECT id FROM documents WHERE status IN ('queued', 'processing') "
            "AND updated_at < %s", (cutoff,))]
    for doc_id in ids:
        q.enqueue({"document_id": doc_id})
    print(f"requeued {len(ids)} document(s)")


def cmd_requeue_dead(args) -> None:
    from .db import open_pool, pool
    from .jobqueue import connect

    q = connect(settings.redis_url)
    for job in q.dead_jobs():
        print(f"  {job['document_id'][:12]}  {job.get('last_error', '')}")
    n = q.requeue_dead()
    if n:
        open_pool()
        with pool.connection() as conn:
            conn.execute("UPDATE documents SET status = 'queued', error = NULL "
                         "WHERE status = 'failed'")
    print(f"requeued {n} dead job(s)")


def cmd_status(args) -> None:
    from . import stats
    from .db import open_pool
    from .jobqueue import connect

    open_pool()
    print("queue:", json.dumps(connect(settings.redis_url).stats()))
    for row in stats.chunk_counts():
        print(f"  {row['course_id']}: {row['chunks']} chunks")
    for d in stats.documents():
        print(f"  [{d['status']:<10}] {d['course_id']}  {d['filename']}  "
              f"pages={d['pages']} chunks={d['chunks']}")


def _retriever():
    from .ingest.embedder import Embedder
    from .retrieval import Retriever
    from .worker import load_classifier

    return Retriever(Embedder(settings.embed_model), router=load_classifier())


def _print_answer(rendered: dict) -> None:
    for p in rendered["parts"]:
        marks = "".join(f"[{n}]" for n in p["refs"])
        print(p["text"] + marks, end="")
    print("\n")
    for s in rendered["sources"]:
        print(f"  [{s['n']}] {s['title']}")
    if rendered.get("served_by"):
        print(f"  (answered by {rendered['served_by']})")


def cmd_ask(args) -> None:
    from . import agent
    from .db import open_pool

    open_pool()
    result = agent.run([], args.question, _retriever())
    if result.refused:
        print("Declined. Try rephrasing.")
        return
    _print_answer(agent.render(result.final))


def cmd_chat(args) -> None:
    from . import agent
    from .db import open_pool

    open_pool()
    retriever, history = _retriever(), []
    print("ask away (ctrl-d to quit)")
    while True:
        try:
            text = input("\n> ").strip()
        except EOFError:
            return
        if not text:
            continue
        result = agent.run(history, text, retriever)
        if result.refused:
            print("Declined. Try rephrasing.")
            continue
        history += result.new_messages
        _print_answer(agent.render(result.final))


def cmd_search(args) -> None:
    from .db import open_pool

    open_pool()
    for h in _retriever().search(args.query, course=args.course, k=args.k, mode=args.mode):
        snippet = " ".join(h.text.split())[:110]
        print(f"{h.score:.4f}  {h.filename} p.{h.page}  {snippet}")


def cmd_quiz(args) -> None:
    """Terminal quiz. Uses the in-memory review heap since one process owns the session."""
    from . import quiz
    from .db import open_pool
    from .review import ReviewQueue

    open_pool()
    session = ReviewQueue()
    for i in range(args.n):
        now = datetime.now(UTC)
        qid = session.pop_due(now)
        q = quiz.load_question(qid) if qid else quiz.next_question(args.course)
        q.setdefault("reason_text", "Review: missed earlier this session")
        print(f"\n({i + 1}/{args.n}) {q['reason_text']}\n{q['question']}")
        choices = q["choices"] or []
        for j, c in enumerate(choices):
            print(f"  {'abcd'[j]}) {c}")
        ans = input("> ").strip()
        if choices and len(ans) == 1 and ans.lower() in "abcd"[: len(choices)]:
            ans = choices["abcd".index(ans.lower())]
        res = quiz.submit_answer(str(q["id"]), ans)
        print(f"score {res['score']}/{res['max_score']}  {res['feedback']}")
        if res["score"] < res["max_score"]:
            print(f"reference: {res['answer']}")
            session.push(str(q["id"]), now + timedelta(minutes=3))


def cmd_retag(args) -> None:
    """Re-run the current classifier over every chunk (after shipping a new one)."""
    import numpy as np
    from psycopg.rows import dict_row

    from .db import open_pool, pool
    from .worker import load_classifier

    clf = load_classifier()
    if clf is None:
        sys.exit(f"no classifier at {settings.classifier_path}")
    open_pool()
    for course in COURSES:
        with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute("SELECT id, embedding FROM chunks WHERE course_id = %s",
                               (course,)).fetchall()
        if not rows:
            continue
        preds = clf.predict(np.stack([np.asarray(r["embedding"]) for r in rows]), course)
        with pool.connection() as conn, conn.cursor() as cur:
            cur.executemany("UPDATE chunks SET topic_id = %s, topic_conf = %s WHERE id = %s",
                            [(t, c, r["id"]) for r, (t, c) in zip(rows, preds, strict=True)])
        print(f"{course}: retagged {len(rows)} chunks")


def cmd_seed(args) -> None:
    from . import seed
    from .db import open_pool

    open_pool()
    if args.clear:
        print("removed", seed.clear())
        return
    if seed.already_seeded():
        sys.exit("sample data is already there; run `seed --clear` first")
    print("added", seed.seed(Path(args.file) if args.file else seed.DEFAULT_FILE, days=args.days))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="exampilot")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ingest", help="register a folder of PDFs/notes")
    p.add_argument("folder")
    p.add_argument("--course", choices=COURSES, required=True)
    p.add_argument("--inline", action="store_true", help="process here instead of via workers")
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("requeue-stuck")
    p.add_argument("--minutes", type=int, default=10)
    p.set_defaults(fn=cmd_requeue_stuck)

    sub.add_parser("requeue-dead").set_defaults(fn=cmd_requeue_dead)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("retag").set_defaults(fn=cmd_retag)
    sub.add_parser("chat").set_defaults(fn=cmd_chat)

    p = sub.add_parser("ask")
    p.add_argument("question")
    p.set_defaults(fn=cmd_ask)

    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--course", choices=COURSES)
    p.add_argument("--k", type=int, default=6)
    p.add_argument("--mode", choices=["hybrid", "vector", "keyword"], default="hybrid")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("quiz")
    p.add_argument("course", choices=COURSES)
    p.add_argument("-n", type=int, default=10)
    p.set_defaults(fn=cmd_quiz)

    p = sub.add_parser("seed", help="fake two weeks of quiz history (no API calls)")
    p.add_argument("--clear", action="store_true", help="remove the sample data again")
    p.add_argument("--file", help="questions JSON (default samples/quiz.json)")
    p.add_argument("--days", type=int, default=14)
    p.set_defaults(fn=cmd_seed)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
