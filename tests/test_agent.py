from types import SimpleNamespace as NS

import pytest

from exampilot import agent


class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        # copy: the agent keeps appending to the same list, the real SDK serialises at call time
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


def fake_client(*responses):
    return NS(beta=NS(messages=FakeMessages(responses)))


class FakeRetriever:
    def __init__(self, hits=None, boom=False):
        self.boom = boom
        self.hits = hits if hits is not None else [
            NS(document_id="d1", filename="lec14.pdf", page=22, course_id="daa",
               text="Dijkstra assumes non-negative weights.")
        ]

    def search(self, query, course=None, k=6):
        if self.boom:
            raise RuntimeError("db down")
        return self.hits


def tool_use(id_, query="dijkstra", course="daa"):
    return NS(type="tool_use", id=id_, name="search_notes", input={"query": query, "course": course})


def answer(text="Because ...", citations=None):
    return NS(stop_reason="end_turn", model="m",
              content=[NS(type="text", text=text, citations=citations)])


def run(client, retriever=None, history=None):
    return agent.run(history or [], "why does dijkstra fail?", retriever or FakeRetriever(),
                     client=client, log=lambda *a: None, today="2026-12-01")


def test_calls_search_then_answers():
    client = fake_client(NS(stop_reason="tool_use", model="m", content=[tool_use("tu_1")]), answer())
    result = run(client)

    second = client.beta.messages.calls[1]["messages"]
    tr = second[-1]["content"][0]
    assert tr["tool_use_id"] == "tu_1"
    assert tr["content"][0]["type"] == "search_result"
    assert tr["content"][0]["citations"] == {"enabled": True}
    assert tr["content"][0]["source"] == "d1/lec14.pdf#page=22"
    assert len(result.new_messages) == 4
    assert not result.refused


def test_parallel_tool_calls_go_back_in_one_message():
    turn = NS(stop_reason="tool_use", model="m",
              content=[tool_use("a", course="daa"), tool_use("b", course="ai")])
    client = fake_client(turn, answer())
    run(client)
    last = client.beta.messages.calls[1]["messages"][-1]
    assert last["role"] == "user"
    assert [r["tool_use_id"] for r in last["content"]] == ["a", "b"]


def test_tool_error_goes_to_model():
    client = fake_client(NS(stop_reason="tool_use", model="m", content=[tool_use("x")]), answer())
    run(client, FakeRetriever(boom=True))
    tr = client.beta.messages.calls[1]["messages"][-1]["content"][0]
    assert tr["is_error"] is True
    assert "db down" in tr["content"]


def test_no_hits_returns_plain_text():
    client = fake_client(NS(stop_reason="tool_use", model="m", content=[tool_use("x")]), answer())
    run(client, FakeRetriever(hits=[]))
    tr = client.beta.messages.calls[1]["messages"][-1]["content"][0]
    assert tr["content"][0]["type"] == "text"


def test_refusal_stores_nothing():
    result = run(fake_client(NS(stop_reason="refusal", model="m", content=[])))
    assert result.refused and result.new_messages == []


def test_step_limit():
    looping = [NS(stop_reason="tool_use", model="m", content=[tool_use(f"t{i}")])
               for i in range(agent.MAX_STEPS)]
    with pytest.raises(RuntimeError, match="didn't finish"):
        run(fake_client(*looping))


def test_date_goes_in_user_turn_not_system():
    client = fake_client(answer())
    run(client)
    call = client.beta.messages.calls[0]
    assert "2026-12-01" not in call["system"]
    assert "2026-12-01" in call["messages"][-1]["content"]


def test_history_is_kept():
    prior = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    client = fake_client(answer())
    result = run(client, history=prior)
    assert client.beta.messages.calls[0]["messages"][:2] == prior
    assert len(result.new_messages) == 2


def test_render_numbers_sources():
    cite = lambda src, q: NS(type="search_result_location", source=src, title=src.upper(),  # noqa: E731
                             cited_text=q)
    resp = NS(model=agent.llm.MODEL, content=[
        NS(type="thinking"),
        NS(type="text", text="A.", citations=[cite("d1/x.pdf#page=1", "q1")]),
        NS(type="text", text=" B.", citations=[cite("d1/x.pdf#page=1", "q1"),
                                               cite("d2/y.pdf#page=3", "q2")]),
        NS(type="text", text=" C.", citations=None),
    ])
    out = agent.render(resp)
    assert [p["refs"] for p in out["parts"]] == [[1], [1, 2], []]
    assert [s["n"] for s in out["sources"]] == [1, 2]
    assert out["served_by"] is None
