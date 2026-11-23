from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from exampilot import bandit

NOW = datetime(2026, 12, 1, tzinfo=UTC)


def test_decay_moves_toward_prior():
    a, b = bandit.decay(11, 3, NOW - timedelta(days=7), NOW)
    assert a == pytest.approx(1 + 10 * 0.85**7)
    assert b == pytest.approx(1 + 2 * 0.85**7)


def test_no_decay_for_future_timestamps():
    assert bandit.decay(5, 5, NOW + timedelta(days=1), NOW) == (5, 5)


def test_partial_credit_splits():
    a, b = bandit.update(1, 1, NOW, 0.5, NOW)
    assert (a, b) == (1.5, 1.5)


def test_prefers_topic_you_keep_failing():
    arms = [
        bandit.Arm("good", alpha=30, beta=1, updated_at=NOW),
        bandit.Arm("bad", alpha=1, beta=30, updated_at=NOW),
    ]
    rng = np.random.default_rng(0)
    picks = [bandit.choose(arms, NOW, rng) for _ in range(200)]
    assert picks.count("bad") > 190


def test_exam_weight_matters():
    arms = [
        bandit.Arm("light", 5, 5, NOW, exam_weight=0.2),
        bandit.Arm("heavy", 5, 5, NOW, exam_weight=2.0),
    ]
    rng = np.random.default_rng(1)
    picks = [bandit.choose(arms, NOW, rng) for _ in range(200)]
    assert picks.count("heavy") > 150


def test_unexplored_topic_gets_tried():
    arms = [bandit.Arm("known_ok", 8, 3, NOW), bandit.Arm("new", 1, 1, NOW)]
    rng = np.random.default_rng(2)
    picks = [bandit.choose(arms, NOW, rng) for _ in range(300)]
    assert 0 < picks.count("new") < 300
