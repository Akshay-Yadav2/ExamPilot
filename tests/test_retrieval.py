from exampilot.retrieval import RRF_K, rrf_merge


def row(i):
    return {"id": i}


def test_item_high_in_both_lists_wins():
    vec = [row("a"), row("b"), row("c")]
    kw = [row("b"), row("d"), row("a")]
    merged = rrf_merge([vec, kw], k=4)
    ids = [r["id"] for r, _ in merged]
    assert ids[0] == "b"
    assert set(ids) == {"a", "b", "c", "d"}


def test_scores_add_up():
    merged = dict((r["id"], s) for r, s in rrf_merge([[row("a")], [row("a")]], k=1))
    assert merged["a"] == 2 / (RRF_K + 1)


def test_k_limits_output():
    assert len(rrf_merge([[row(str(i)) for i in range(50)]], k=6)) == 6


def test_empty():
    assert rrf_merge([[], []], k=5) == []
