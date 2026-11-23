import logging
from pathlib import PurePath

from .. import storage
from ..db import pool
from .chunker import chunk_pages
from .embedder import Embedder
from .extract import empty_pages, markdown_pages, pdf_pages

log = logging.getLogger(__name__)


def process_document(job: dict, embedder: Embedder, classifier=None) -> int:
    """Safe to run twice for the same document. Returns the number of chunks written."""
    doc_id = job["document_id"]
    with pool.connection() as conn:
        row = conn.execute(
            "UPDATE documents SET status = 'processing', updated_at = now() "
            "WHERE id = %s AND status <> 'done' RETURNING filename, course_id, path",
            (doc_id,),
        ).fetchone()
    if row is None:
        log.info("document %s already done or gone, skipping", doc_id)
        return 0
    filename, course_id, path = row

    data = storage.load(path)
    if PurePath(filename).suffix.lower() == ".md":
        pages = markdown_pages(data.decode("utf-8", errors="replace"))
    else:
        pages = pdf_pages(data)

    blank = empty_pages(pages)
    if blank:
        log.warning("%s: %d of %d pages have no text (scanned?)", filename, blank, len(pages))

    chunks = chunk_pages(doc_id, course_id, filename, pages, embedder.count_tokens)
    if not chunks:
        raise ValueError(f"{filename}: no text extracted ({len(pages)} pages)")

    vectors = embedder.encode([c.embed_text for c in chunks])
    if classifier is not None:
        topics = classifier.predict(vectors, course_id)
    else:
        topics = [(None, None)] * len(chunks)

    rows = [
        (c.id, c.document_id, c.course_id, c.page, c.idx, c.text, c.tokens,
         topic, conf, embedder.name, vec)
        for c, vec, (topic, conf) in zip(chunks, vectors, topics, strict=True)
    ]

    # chunks + 'done' commit together, or not at all
    with pool.connection() as conn, conn.transaction():
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (id, document_id, course_id, page, idx, text, tokens, "
                "topic_id, topic_conf, embed_model, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                rows,
            )
        conn.execute(
            "UPDATE documents SET status = 'done', pages = %s, error = NULL, updated_at = now() "
            "WHERE id = %s",
            (len(pages), doc_id),
        )

    log.info("ingested %s: %d pages, %d chunks", filename, len(pages), len(chunks))
    return len(chunks)
