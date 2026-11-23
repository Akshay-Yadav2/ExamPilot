from collections import defaultdict
from dataclasses import asdict, dataclass

import numpy as np
from psycopg.rows import dict_row

from .db import pool
from .lru import LRUCache

RRF_K = 60

VECTOR_SQL = """
SELECT c.id, c.document_id, c.page, c.text, c.course_id, c.topic_id, d.filename
FROM chunks c JOIN documents d ON d.id = c.document_id
WHERE (%(course)s::text IS NULL OR c.course_id = %(course)s)
ORDER BY c.embedding <=> %(qvec)s
LIMIT %(k)s
"""

# OR the terms together. websearch_to_tsquery ANDs every word, so a full
# question ("why does dijkstra fail with...") almost never matched anything.
# ts_rank_cd still puts chunks that hit more of the terms first.
KEYWORD_SQL = """
SELECT c.id, c.document_id, c.page, c.text, c.course_id, c.topic_id, d.filename
FROM chunks c
JOIN documents d ON d.id = c.document_id,
     to_tsquery('english', replace(plainto_tsquery('english', %(q)s)::text, ' & ', ' | ')) query
WHERE c.tsv @@ query
  AND (%(course)s::text IS NULL OR c.course_id = %(course)s)
ORDER BY ts_rank_cd(c.tsv, query) DESC
LIMIT %(k)s
"""


@dataclass
class Hit:
    id: str
    document_id: str
    filename: str
    page: int
    text: str
    course_id: str
    topic_id: str | None
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


def rrf_merge(result_lists: list[list[dict]], k: int) -> list[tuple[dict, float]]:
    """Reciprocal rank fusion. Cosine and ts_rank aren't on the same scale, ranks are."""
    scores: dict[str, float] = defaultdict(float)
    rows: dict[str, dict] = {}
    for results in result_lists:
        for rank, row in enumerate(results, start=1):
            scores[row["id"]] += 1.0 / (RRF_K + rank)
            rows[row["id"]] = row
    best = sorted(scores, key=lambda i: scores[i], reverse=True)[:k]
    return [(rows[i], scores[i]) for i in best]


class Retriever:
    def __init__(self, embedder, router=None, cache_size: int = 512, query_prefix: bool = True):
        self.embedder = embedder
        self.router = router  # optional classifier: picks a course when none is given
        self.cache = LRUCache(cache_size)
        self.query_prefix = query_prefix

    def _qvec(self, query: str) -> np.ndarray:
        key = " ".join(query.lower().split())
        vec = self.cache.get(key)
        if vec is None:
            vec = self.embedder.encode_query(query, prefix=self.query_prefix)
            self.cache.put(key, vec)
        return vec

    def search(
        self,
        query: str,
        course: str | None = None,
        k: int = 6,
        mode: str = "hybrid",
        pool_k: int = 30,
    ) -> list[Hit]:
        qvec = self._qvec(query)
        if course is None and self.router is not None:
            course = self.router.route(qvec)  # None unless it's fairly sure

        params = {"q": query, "qvec": qvec, "course": course, "k": pool_k}
        lists = []
        with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            if mode in ("hybrid", "vector"):
                lists.append(cur.execute(VECTOR_SQL, params).fetchall())
            if mode in ("hybrid", "keyword"):
                lists.append(cur.execute(KEYWORD_SQL, params).fetchall())
        return [Hit(**row, score=s) for row, s in rrf_merge(lists, k)]
