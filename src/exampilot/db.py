from psycopg import Connection
from psycopg_pool import ConnectionPool

from .config import settings


def _configure(conn: Connection) -> None:
    from pgvector.psycopg import register_vector

    register_vector(conn)
    # default is 40, which drops rows once a course filter is applied
    conn.execute("SET hnsw.ef_search = 100")


# autocommit on; anything that needs atomicity uses `with conn.transaction():`
pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"autocommit": True},
    configure=_configure,
    open=False,
)


def open_pool() -> None:
    pool.open(wait=True)
