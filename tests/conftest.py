import os

import pytest


def word_count(s: str) -> int:
    return len(s.split())


@pytest.fixture
def count():
    return word_count


@pytest.fixture
def redis_client():
    redis = pytest.importorskip("redis")
    r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/15"),
                             decode_responses=True)
    try:
        r.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip("redis not running")
    r.flushdb()
    yield r
    r.flushdb()
