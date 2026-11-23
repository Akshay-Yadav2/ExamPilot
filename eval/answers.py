"""Answer eval: run the real agent, then judge. Costs money, so it's on demand.

    python -m eval.answers eval/questions.jsonl --out eval-report.json --min-score 0.75
"""

import argparse
import json
import statistics
import sys
import time

from pydantic import BaseModel

JUDGE_SYSTEM = """You check a study assistant's answer against a list of key points and the course excerpts.
For each key point, in order, say whether the answer covers it (same idea, any wording).
Flag contradicts_material if the answer states something the excerpts contradict.
Set says_not_in_material if the answer says the course material doesn't cover the question."""


class Judgment(BaseModel):
    key_points_covered: list[bool]
    contradicts_material: bool
    says_not_in_material: bool


def judge(q: dict, answer_text: str, excerpts: str, client) -> Judgment:
    from exampilot import llm

    points = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(q["key_points"])) or "(none)"
    started = time.perf_counter()
    resp = client.messages.parse(
        model=llm.MODEL,
        max_tokens=8000,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": (
            f"Question: {q['question']}\n\nKey points:\n{points}\n\n"
            f"Course excerpts:\n{excerpts or '(none)'}\n\n<answer>\n{answer_text}\n</answer>")}],
        output_format=Judgment,
    )
    llm.log_call("judge", resp, started)
    return resp.parsed_output


def score(q: dict, j: Judgment) -> float:
    if not q["answerable"]:
        return 1.0 if j.says_not_in_material else 0.0
    if j.contradicts_material or not j.key_points_covered:
        return 0.0
    return sum(j.key_points_covered) / len(j.key_points_covered)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions")
    ap.add_argument("--out", default="eval-report.json")
    ap.add_argument("--min-score", type=float, default=0.0)
    args = ap.parse_args()

    from eval.retrieval import load
    from exampilot import agent, llm
    from exampilot.config import settings
    from exampilot.db import open_pool
    from exampilot.ingest.embedder import Embedder
    from exampilot.retrieval import Retriever

    open_pool()
    client = llm.get_client()
    retriever = Retriever(Embedder(settings.embed_model))
    rows = []

    for q in load(args.questions):
        t0 = time.perf_counter()
        costs: list[float] = []

        def log(kind, resp, started, costs=costs):
            costs.append(llm.cost_usd(resp.model, resp.usage))
            llm.log_call(kind, resp, started)

        result = agent.run([], q["question"], retriever, log=log)
        latency = time.perf_counter() - t0
        rendered = agent.render(result.final)
        text = "".join(p["text"] for p in rendered["parts"])
        cited = {(s["source"].split("/", 1)[1].split("#")[0],
                  int(s["source"].rsplit("=", 1)[1])) for s in rendered["sources"]}
        gold = {(g["file"], g["page"]) for g in q["gold"]}
        excerpts = "\n\n".join(s["quote"] for s in rendered["sources"])

        j = judge(q, text, excerpts, client)
        rows.append({
            "id": q["id"], "answerable": q["answerable"], "score": score(q, j),
            "citation_hit": bool(cited & gold) if q["answerable"] else None,
            "abstained": (not cited and j.says_not_in_material) if not q["answerable"] else None,
            "cost_usd": round(sum(costs), 5), "latency_s": round(latency, 2),
        })
        print(f"{q['id']:<8} score={rows[-1]['score']:.2f} ${rows[-1]['cost_usd']:.4f} "
              f"{latency:.1f}s")

    ans = [r for r in rows if r["answerable"]]
    unans = [r for r in rows if not r["answerable"]]
    lat = sorted(r["latency_s"] for r in rows)
    summary = {
        "n": len(rows),
        "answer_score": round(statistics.mean(r["score"] for r in ans), 3) if ans else None,
        "citation_hit": round(statistics.mean(r["citation_hit"] for r in ans), 3) if ans else None,
        "abstention": round(statistics.mean(r["abstained"] for r in unans), 3) if unans else None,
        "cost_per_answer": round(statistics.mean(r["cost_usd"] for r in rows), 4),
        "latency_p50": lat[len(lat) // 2],
        "latency_p95": lat[min(len(lat) - 1, int(len(lat) * 0.95))],
    }
    print(json.dumps(summary, indent=2))
    with open(args.out, "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=2)
    if (summary["answer_score"] or 0) < args.min_score:
        sys.exit(1)


if __name__ == "__main__":
    main()
