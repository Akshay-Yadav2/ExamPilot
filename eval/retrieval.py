"""Retrieval eval: recall@k and MRR@10. No API calls, so CI runs it on every push.

    python -m eval.retrieval eval/questions.jsonl --min-recall 0.8
    python -m eval.retrieval eval/questions.jsonl --all-modes
"""

import argparse
import json
import sys
from collections import defaultdict


def load(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate(retriever, questions: list[dict], k: int = 5, mode: str = "hybrid") -> dict:
    answerable = [q for q in questions if q["answerable"]]
    hits_at_k, rr = 0, 0.0
    per_course = defaultdict(lambda: [0, 0])
    for q in answerable:
        gold = {(g["file"], g["page"]) for g in q["gold"]}
        results = retriever.search(q["question"], course=q["course"], k=10, mode=mode)
        ranks = [i for i, h in enumerate(results, start=1) if (h.filename, h.page) in gold]
        hit = bool(ranks) and ranks[0] <= k
        hits_at_k += hit
        rr += 1 / ranks[0] if ranks else 0.0
        per_course[q["course"]][0] += hit
        per_course[q["course"]][1] += 1

    n = len(answerable) or 1
    return {
        "mode": mode,
        f"recall@{k}": round(hits_at_k / n, 3),
        "mrr@10": round(rr / n, 3),
        "n": len(answerable),
        "by_course": {c: round(h / t, 3) for c, (h, t) in per_course.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--min-recall", type=float, default=0.0)
    ap.add_argument("--all-modes", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    from exampilot.config import settings
    from exampilot.db import open_pool
    from exampilot.ingest.embedder import Embedder
    from exampilot.retrieval import Retriever

    open_pool()
    retriever = Retriever(Embedder(settings.embed_model))
    questions = load(args.questions)
    modes = ["vector", "keyword", "hybrid"] if args.all_modes else ["hybrid"]

    results = [evaluate(retriever, questions, args.k, m) for m in modes]
    print(f"{'mode':<9} {'recall@' + str(args.k):>9} {'mrr@10':>7}   per course")
    for r in results:
        print(f"{r['mode']:<9} {r[f'recall@{args.k}']:>9.3f} {r['mrr@10']:>7.3f}   {r['by_course']}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)

    hybrid = next(r for r in results if r["mode"] == "hybrid")
    if hybrid[f"recall@{args.k}"] < args.min_recall:
        print(f"FAIL: recall@{args.k} {hybrid[f'recall@{args.k}']} < {args.min_recall}")
        sys.exit(1)


if __name__ == "__main__":
    main()
