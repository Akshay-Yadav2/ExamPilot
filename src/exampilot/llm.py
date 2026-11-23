import logging
import time
from functools import cache

import anthropic

from .config import settings

log = logging.getLogger(__name__)

MODEL = settings.model

# $ per million tokens. Check the pricing page before quoting these anywhere.
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.20, "cache_write": 5.00},
}


@cache
def get_client() -> anthropic.Anthropic:
    # SDK already retries 429 / 5xx / connection errors with backoff
    return anthropic.Anthropic(max_retries=3)


def cost_usd(model: str, usage) -> float:
    p = PRICES.get(model)
    if p is None:
        return 0.0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    total = (
        usage.input_tokens * p["input"]
        + usage.output_tokens * p["output"]
        + cache_read * p["cache_read"]
        + cache_write * p["cache_write"]
    )
    return total / 1_000_000


def log_call(kind: str, response, started: float) -> None:
    # logging must never take down the request it's logging
    try:
        from .db import pool

        u = response.usage
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO llm_calls (kind, model, input_tokens, output_tokens, "
                "cache_read_tokens, cache_write_tokens, latency_ms, cost_usd, stop_reason, "
                "request_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    kind,
                    response.model,
                    u.input_tokens,
                    u.output_tokens,
                    getattr(u, "cache_read_input_tokens", 0) or 0,
                    getattr(u, "cache_creation_input_tokens", 0) or 0,
                    int((time.perf_counter() - started) * 1000),
                    cost_usd(response.model, u),
                    response.stop_reason,
                    getattr(response, "_request_id", None),
                ),
            )
    except Exception:  # noqa: BLE001
        log.exception("couldn't log llm call")
