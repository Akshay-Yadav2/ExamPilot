from exampilot.ingest.extract import clean_pages, empty_pages, markdown_pages


def test_removes_repeated_footer_and_page_numbers():
    pages = [f"CS-GY 6033 Fall 2026\nTopic {i}\n{i}" for i in range(1, 9)]
    out = clean_pages(pages)
    assert all("CS-GY" not in p for p in out)
    assert out[0] == "Topic 1"


def test_rejoins_hyphenated_words():
    (out,) = clean_pages(["dyna-\nmic programming"])
    assert out == "dynamic programming"


def test_markdown_sections_become_pages():
    md = "# Week 1\nintro\n\n## Greedy\nstuff\n### detail\nmore\n# Week 2\nend"
    pages = markdown_pages(md)
    assert len(pages) == 3
    assert pages[1].startswith("## Greedy") and "### detail" in pages[1]


def test_counts_scanned_pages():
    assert empty_pages(["text", "", "", "more"]) == 2


def test_bare_title_merges_into_next_section():
    pages = markdown_pages("# Design principles\n\n## SOLID\nfive rules\n## Coupling\nless is more")
    assert len(pages) == 2
    assert pages[0].startswith("# Design principles") and "## SOLID" in pages[0]


def test_trailing_bare_title_kept():
    assert markdown_pages("## A\ntext\n# Appendix") == ["## A\ntext", "# Appendix"]
