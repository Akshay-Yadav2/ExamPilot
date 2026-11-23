import re
from collections import Counter

PAGE_NUM = re.compile(r"^\s*(page\s*)?\d+\s*(/\s*\d+)?\s*$", re.I)


def pdf_pages(data: bytes) -> list[str]:
    """Cleaned text for every page, index 0 is page 1."""
    import pymupdf

    with pymupdf.open(stream=data, filetype="pdf") as doc:
        raw = [page.get_text("text") for page in doc]
    return clean_pages(raw)


def markdown_pages(text: str) -> list[str]:
    # each # / ## section counts as a "page" so citations still point somewhere useful
    parts = [p.strip() for p in re.split(r"(?m)^(?=#{1,2} )", text) if p.strip()]
    pages: list[str] = []
    carry = ""
    for part in parts:
        if "\n" not in part and part.startswith("#"):
            carry += part + "\n\n"  # a bare title goes on top of the next section
            continue
        pages.append(carry + part)
        carry = ""
    if carry:
        pages.append(carry.strip())
    return pages


def clean_pages(pages: list[str]) -> list[str]:
    lines_per_page = [[ln.strip() for ln in p.splitlines() if ln.strip()] for p in pages]

    # Anything on more than half the pages is a header/footer: course code,
    # professor's name, "Fall 2026", etc. These wreck keyword search otherwise.
    counts = Counter(ln for lines in lines_per_page for ln in set(lines))
    threshold = max(3, len(pages) // 2)
    boilerplate = {ln for ln, c in counts.items() if c >= threshold}

    out = []
    for lines in lines_per_page:
        kept = [ln for ln in lines if ln not in boilerplate and not PAGE_NUM.match(ln)]
        text = "\n".join(kept)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # hyphenated line breaks
        text = re.sub(r"[ \t]+", " ", text)
        out.append(text.strip())
    return out


def empty_pages(pages: list[str]) -> int:
    """Scanned decks come back as blank pages; worth reporting instead of indexing nothing."""
    return sum(1 for p in pages if not p)
