import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass

SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])")


@dataclass
class Chunk:
    id: str
    document_id: str
    course_id: str
    page: int
    idx: int
    text: str
    tokens: int
    embed_text: str


def chunk_id(document_id: str, page: int, idx: int) -> str:
    return hashlib.sha256(f"{document_id}:{page}:{idx}".encode()).hexdigest()[:32]


def split_units(text: str, count: Callable[[str], int], max_tokens: int) -> list[str]:
    """Paragraphs first, then sentences, then hard word splits if a sentence is still huge."""
    units: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if count(para) <= max_tokens:
            units.append(para)
            continue
        for sent in SENTENCE_END.split(para):
            if count(sent) <= max_tokens:
                units.append(sent)
                continue
            words = sent.split()
            step = max(1, max_tokens // 2)  # assume ~2 tokens/word in the worst case
            units.extend(" ".join(words[i : i + step]) for i in range(0, len(words), step))
    return units


def chunk_pages(
    document_id: str,
    course_id: str,
    filename: str,
    pages: list[str],
    count: Callable[[str], int],
    max_tokens: int = 300,
    overlap: int = 50,
) -> list[Chunk]:
    """Greedy packing inside each page. A chunk never spans two pages, so every
    citation lands on exactly one page."""
    chunks: list[Chunk] = []

    def make(page_no: int, idx: int, parts: list[str]) -> Chunk:
        body = "\n".join(parts)
        return Chunk(
            id=chunk_id(document_id, page_no, idx),
            document_id=document_id,
            course_id=course_id,
            page=page_no,
            idx=idx,
            text=body,
            tokens=count(body),
            # filename gives short slides like "Proof (cont.)" some context
            embed_text=f"{filename} · p.{page_no}\n{body}",
        )

    for page_no, text in enumerate(pages, start=1):
        if not text:
            continue
        buf: list[str] = []
        buf_tokens = 0
        idx = 0

        for unit in split_units(text, count, max_tokens):
            t = count(unit)
            if buf and buf_tokens + t > max_tokens:
                chunks.append(make(page_no, idx, buf))
                idx += 1
                tail, tail_tokens = [], 0
                for u in reversed(buf):
                    ut = count(u)
                    if tail_tokens + ut > overlap:
                        break
                    tail.insert(0, u)
                    tail_tokens += ut
                # don't let overlap + next unit blow past the limit
                while tail and tail_tokens + t > max_tokens:
                    tail_tokens -= count(tail.pop(0))
                buf, buf_tokens = tail, tail_tokens
            buf.append(unit)
            buf_tokens += t
        if buf:
            chunks.append(make(page_no, idx, buf))

    return chunks
