"""Discounted Thompson sampling over topics.

Reward is *finding a question you get wrong*, so each topic keeps a Beta
posterior over P(wrong). Old evidence fades toward the prior by GAMMA per day,
because practising a topic changes how good you are at it.
"""

from dataclasses import dataclass
from datetime import datetime

import numpy as np

GAMMA_PER_DAY = 0.85  # a week-old answer counts ~0.32 of today's


@dataclass
class Arm:
    topic_id: str
    alpha: float  # 1 + discounted correct
    beta: float  # 1 + discounted wrong
    updated_at: datetime
    exam_weight: float = 1.0


def decay(alpha: float, beta: float, updated_at: datetime, now: datetime,
          gamma: float = GAMMA_PER_DAY) -> tuple[float, float]:
    days = max(0.0, (now - updated_at).total_seconds() / 86400)
    f = gamma**days
    return 1 + (alpha - 1) * f, 1 + (beta - 1) * f


def update(alpha: float, beta: float, updated_at: datetime, frac_correct: float,
           now: datetime) -> tuple[float, float]:
    """frac_correct: 1 correct, 0.5 partial, 0 wrong."""
    alpha, beta = decay(alpha, beta, updated_at, now)
    return alpha + frac_correct, beta + (1 - frac_correct)


def choose(arms: list[Arm], now: datetime, rng: np.random.Generator) -> str:
    if not arms:
        raise ValueError("no topics to choose from")
    best_topic, best_value = arms[0].topic_id, -1.0
    for arm in arms:
        a, b = decay(arm.alpha, arm.beta, arm.updated_at, now)
        value = arm.exam_weight * rng.beta(b, a)  # sampled P(wrong), weighted
        if value > best_value:
            best_topic, best_value = arm.topic_id, value
    return best_topic
