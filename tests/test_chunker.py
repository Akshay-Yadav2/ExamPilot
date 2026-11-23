from exampilot.ingest.chunker import chunk_pages, split_units


def test_never_crosses_pages(count):
    pages = ["alpha beta gamma. " * 50, "delta epsilon. " * 50]
    chunks = chunk_pages("doc", "daa", "f.pdf", pages, count, max_tokens=40, overlap=10)
    assert {c.page for c in chunks} == {1, 2}
    for c in chunks:
        src = pages[c.page - 1]
        assert all(word in src for word in c.text.split())


def test_respects_max_tokens(count):
    pages = ["One two three four five. " * 80]
    chunks = chunk_pages("doc", "daa", "f.pdf", pages, count, max_tokens=30, overlap=8)
    assert chunks
    assert all(c.tokens <= 30 for c in chunks)


def test_overlap_carries_tail(count):
    sents = [f"Sentence number {i} is here." for i in range(30)]
    chunks = chunk_pages("doc", "daa", "f.pdf", [" ".join(sents)], count, max_tokens=25, overlap=10)
    assert len(chunks) > 1
    first, second = chunks[0].text.split("\n"), chunks[1].text.split("\n")
    # the last couple of sentences of chunk 0 open chunk 1
    shared = [s for s in second if s in first]
    assert shared and shared == first[-len(shared):]
    assert second[: len(shared)] == shared


def test_empty_page_skipped(count):
    chunks = chunk_pages("doc", "daa", "f.pdf", ["", "hello there"], count)
    assert [c.page for c in chunks] == [2]


def test_giant_paragraph_without_periods(count):
    text = " ".join(["word"] * 900)
    units = split_units(text, count, max_tokens=300)
    assert all(count(u) <= 300 for u in units)
    assert sum(count(u) for u in units) == 900


def test_exactly_max_tokens_is_one_chunk(count):
    text = " ".join(["w"] * 300)
    chunks = chunk_pages("doc", "daa", "f.pdf", [text], count, max_tokens=300)
    assert len(chunks) == 1


def test_overlap_bigger_than_a_unit(count):
    paras = "\n\n".join(" ".join(["x"] * 20) for _ in range(6))
    chunks = chunk_pages("doc", "daa", "f.pdf", [paras], count, max_tokens=45, overlap=200)
    assert all(c.tokens <= 45 for c in chunks)


def test_ids_are_deterministic(count):
    a = chunk_pages("doc", "daa", "f.pdf", ["some text here"], count)
    b = chunk_pages("doc", "daa", "f.pdf", ["some text here"], count)
    assert [c.id for c in a] == [c.id for c in b]


def test_embed_text_has_filename(count):
    (c,) = chunk_pages("doc", "daa", "lec14.pdf", ["Proof (cont.)"], count)
    assert c.embed_text.startswith("lec14.pdf · p.1")
    assert c.text == "Proof (cont.)"
