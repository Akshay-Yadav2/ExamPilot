from datetime import UTC, date, datetime, timedelta

import pytest

from exampilot.review import ReviewQueue, cap_for_exam, next_interval

NOW = datetime(2026, 12, 1, 9, tzinfo=UTC)


def test_wrong_resets():
    assert next_interval(10, 2.5, 4, 0.0) == pytest.approx((1.0, 2.3, 0))


def test_ease_floor():
    _, ease, _ = next_interval(1, 1.3, 0, 0)
    assert ease == 1.3


def test_growing_intervals():
    i, e, r = next_interval(0, 2.5, 0, 1.0)
    assert (i, r) == (1.0, 1)
    i, e, r = next_interval(i, e, r, 1.0)
    assert (i, r) == (3.0, 2)
    i, e, r = next_interval(i, e, r, 1.0)
    assert i == pytest.approx(3.0 * 2.7)


def test_nothing_scheduled_after_exam():
    assert cap_for_exam(30, NOW, date(2026, 12, 5)) == 2.0
    assert cap_for_exam(30, NOW, date(2026, 12, 1)) == 0.5
    assert cap_for_exam(30, NOW, None) == 30


def test_heap_pops_in_due_order():
    q = ReviewQueue()
    q.push("b", NOW - timedelta(hours=1))
    q.push("a", NOW - timedelta(hours=2))
    q.push("c", NOW + timedelta(hours=1))
    assert q.pop_due(NOW) == "a"
    assert q.pop_due(NOW) == "b"
    assert q.pop_due(NOW) is None
    assert len(q) == 1


def test_reschedule_skips_stale_entry():
    q = ReviewQueue()
    q.push("x", NOW - timedelta(hours=1))
    q.push("x", NOW + timedelta(days=2))
    assert q.pop_due(NOW) is None
    assert q.pop_due(NOW + timedelta(days=3)) == "x"
    assert len(q) == 0
