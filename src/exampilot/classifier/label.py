"""Claude labels a sample of chunks once; TopicNet learns from those labels.

    python -m exampilot.classifier.label --per-course 200 --out data/labels.jsonl
"""

import argparse
import json
import time

from psycopg.rows import dict_row

from .. import llm
from ..config import COURSES
from ..db import open_pool, pool

LABEL_SYSTEM = """You label excerpts from course material with the single course topic they are mainly about.
If the excerpt is administrative (logistics, grading policy, title slide) or fits no topic, answer "other"."""


def label_chunk(text: str, course: str, topics: list[tuple[str, str]], client=None) -> str | None:
    client = client or llm.get_client()
    topic_list = "\n".join(f"- {tid}: {name}" for tid, name in topics)
    schema = {
        "type": "object",
        "properties": {"topic": {"type": "string", "enum": [t for t, _ in topics] + ["other"]}},
        "required": ["topic"],
        "additionalProperties": False,
    }
    started = time.perf_counter()
    response = client.messages.create(
        model=llm.MODEL,
        max_tokens=4000,
        system=LABEL_SYSTEM,
        messages=[{"role": "user",
                   "content": f"Course: {course}\nTopics:\n{topic_list}\n\nExcerpt:\n{text}"}],
        output_config={"format": {"type": "json_schema", "schema": schema}, "effort": "low"},
    )
    llm.log_call("label", response, started)
    if response.stop_reason != "end_turn":
        return None
    block = next(b for b in response.content if b.type == "text")
    topic = json.loads(block.text)["topic"]
    return None if topic == "other" else topic


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-course", type=int, default=200)
    ap.add_argument("--out", default="data/labels.jsonl")
    args = ap.parse_args()

    open_pool()
    with open(args.out, "a") as out:
        for course in COURSES:
            with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                topics = [(r["id"], r["name"]) for r in cur.execute(
                    "SELECT id, name FROM topics WHERE course_id = %s ORDER BY id", (course,))]
                chunks = cur.execute(
                    "SELECT id, text FROM chunks WHERE course_id = %s AND tokens >= 40 "
                    "ORDER BY random() LIMIT %s",
                    (course, args.per_course),
                ).fetchall()
            for i, c in enumerate(chunks, 1):
                topic = label_chunk(c["text"], course, topics)
                out.write(json.dumps({"chunk_id": c["id"], "course": course, "topic": topic}) + "\n")
                out.flush()
                if i % 25 == 0:
                    print(f"{course}: {i}/{len(chunks)}")


if __name__ == "__main__":
    main()
