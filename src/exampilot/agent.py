"""Chat agent: a hand-written tool loop on the Messages API.

Only chat is an agent. Quiz generation and grading always run the same steps,
so they're single structured calls (see quiz.py).
"""

import json
import time
from dataclasses import dataclass
from datetime import date

from . import llm

MAX_STEPS = 6

# Keep this byte-for-byte stable (no dates, ids, counts) or prompt caching misses.
SYSTEM = """You are ExamPilot, a study assistant for one graduate student preparing for three final exams:
- swe: Software Engineering
- ai: Artificial Intelligence
- daa: Design and Analysis of Algorithms

How to answer:
- For any question about course content, call search_notes first and answer from what it returns. The course material is the authority: use its definitions and notation, even where other sources differ.
- If the results don't cover the question, search again with different words (for example the formal name of the concept, or the name of the algorithm). If the material still doesn't cover it, say so plainly, then give a short general answer and label it as not from the course material.
- Keep answers short and exam-oriented: the definition, the key idea, a small example, and the common mistake when there is one.
- When the student asks what to study or how they are doing, use weakest_topics and recent_mistakes."""

TOOLS = [
    {
        "name": "search_notes",
        "description": (
            "Search the student's course material (lecture slides, textbook chapters, practice "
            "exams, study notes) and return the most relevant passages with file name and page. "
            "Use it before answering any question about course content. Call it again with "
            "different words if the first results don't answer the question."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look for. Include key terms."},
                "course": {
                    "type": "string",
                    "enum": ["daa", "swe", "ai", "any"],
                    "description": "The course to search, or 'any' if unclear.",
                },
            },
            "required": ["query", "course"],
            "additionalProperties": False,
        },
    },
    {
        "name": "weakest_topics",
        "description": (
            "The student's five weakest topics from quiz history: recency-weighted mastery "
            "(0 to 1), number of attempts, and priority (exam weight times weakness)."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"course": {"type": "string", "enum": ["daa", "swe", "ai", "all"]}},
            "required": ["course"],
            "additionalProperties": False,
        },
    },
    {
        "name": "recent_mistakes",
        "description": (
            "The student's most recent wrong or partly wrong quiz answers, with the question, "
            "the reference answer, what they wrote, and the grader's feedback."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"course": {"type": "string", "enum": ["daa", "swe", "ai", "all"]}},
            "required": ["course"],
            "additionalProperties": False,
        },
    },
]


def _course(value: str) -> str | None:
    return None if value in ("any", "all") else value


def search_result_blocks(hits) -> list[dict]:
    if not hits:
        return [{"type": "text", "text": "No results found in the course material."}]
    return [
        {
            "type": "search_result",
            # doc id first so the front end can turn a citation into /files/<id>#page=N
            "source": f"{h.document_id}/{h.filename}#page={h.page}",
            "title": f"{h.course_id.upper()} · {h.filename} · p.{h.page}",
            "content": [{"type": "text", "text": h.text}],
            "citations": {"enabled": True},
        }
        for h in hits
    ]


def run_tool(block, retriever, stats_mod=None) -> dict:
    if stats_mod is None:
        from . import stats as stats_mod
    try:
        course = _course(block.input["course"])
        if block.name == "search_notes":
            content = search_result_blocks(retriever.search(block.input["query"], course=course, k=6))
        elif block.name == "weakest_topics":
            content = json.dumps(stats_mod.weakest_topics(course), default=str)
        elif block.name == "recent_mistakes":
            content = json.dumps(stats_mod.recent_mistakes(course), default=str)
        else:
            raise ValueError(f"unknown tool: {block.name}")
        return {"type": "tool_result", "tool_use_id": block.id, "content": content}
    except Exception as e:  # noqa: BLE001 - let the model see it and try again
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Error: {e}",
            "is_error": True,
        }


@dataclass
class AgentResult:
    new_messages: list[dict]  # what to append to the stored conversation; empty on refusal
    final: object
    refused: bool = False


def run(history: list[dict], user_text: str, retriever, client=None, log=llm.log_call,
        today: str | None = None, stats_mod=None) -> AgentResult:
    client = client or llm.get_client()
    today = today or date.today().isoformat()
    # date lives in the user turn, not the system prompt, so the cached prefix doesn't change
    messages = [*history, {"role": "user", "content": f"(Today is {today}.)\n\n{user_text}"}]
    first_new = len(history)

    for _ in range(MAX_STEPS):
        started = time.perf_counter()
        response = client.beta.messages.create(
            model=llm.MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
            cache_control={"type": "ephemeral"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        log("chat", response, started)

        if response.stop_reason == "refusal":
            return AgentResult(new_messages=[], final=response, refused=True)
        if response.stop_reason == "max_tokens" and any(
            b.type == "tool_use" for b in response.content
        ):
            raise RuntimeError("output cut off in the middle of a tool call, raise max_tokens")

        # whole turn goes back unchanged, thinking blocks included
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            # every result for this turn goes back in ONE user message
            results = [
                run_tool(b, retriever, stats_mod) for b in response.content if b.type == "tool_use"
            ]
            messages.append({"role": "user", "content": results})
            continue
        if response.stop_reason == "pause_turn":
            continue
        return AgentResult(new_messages=messages[first_new:], final=response)

    raise RuntimeError(f"agent didn't finish in {MAX_STEPS} steps")


def render(response) -> dict:
    """Final answer -> text parts with footnote numbers + a list of sources."""
    sources: dict[str, dict] = {}
    parts = []
    for block in response.content:
        if block.type != "text":
            continue
        refs = []
        for c in getattr(block, "citations", None) or []:
            if c.type != "search_result_location":
                continue
            if c.source not in sources:
                sources[c.source] = {
                    "n": len(sources) + 1,
                    "source": c.source,
                    "title": c.title,
                    "quote": c.cited_text[:400],
                }
            refs.append(sources[c.source]["n"])
        parts.append({"text": block.text, "refs": sorted(set(refs))})

    fell_back = any(getattr(b, "type", None) == "fallback" for b in response.content)
    served_by = response.model if fell_back or response.model != llm.MODEL else None
    return {"parts": parts, "sources": list(sources.values()), "served_by": served_by}


def to_jsonable(content) -> list | str:
    """SDK blocks -> plain dicts, so a reloaded conversation sends the same bytes."""
    if isinstance(content, str):
        return content
    return [b.to_dict(mode="json") if hasattr(b, "to_dict") else b for b in content]
