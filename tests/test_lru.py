import random

import pytest

from exampilot.lru import LRUCache


class Node:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key=None, val=None):
        self.key, self.val, self.prev, self.next = key, val, None, None


class LinkedLRU:
    """Hash map + doubly linked list, the LeetCode 146 way."""

    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}
        self.head, self.tail = Node(), Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, n):
        n.prev.next, n.next.prev = n.next, n.prev

    def _push_front(self, n):
        n.next, n.prev = self.head.next, self.head
        self.head.next.prev = n
        self.head.next = n

    def get(self, key):
        n = self.map.get(key)
        if n is None:
            return None
        self._unlink(n)
        self._push_front(n)
        return n.val

    def put(self, key, val):
        if key in self.map:
            n = self.map[key]
            n.val = val
            self._unlink(n)
        else:
            n = self.map[key] = Node(key, val)
            if len(self.map) > self.cap:
                lru = self.tail.prev
                self._unlink(lru)
                del self.map[lru.key]
        self._push_front(n)


def test_evicts_least_recent():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert c.get("b") is None
    assert c.get("a") == 1 and c.get("c") == 3


def test_counts_hits_and_misses():
    c = LRUCache(1)
    c.get("x")
    c.put("x", 1)
    c.get("x")
    assert (c.hits, c.misses) == (1, 1)


def test_rejects_zero_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)


def test_matches_linked_list_version():
    rng = random.Random(0)
    a, b = LRUCache(16), LinkedLRU(16)
    for _ in range(10_000):
        key = str(rng.randint(0, 40))
        if rng.random() < 0.5:
            assert a.get(key) == b.get(key)
        else:
            v = rng.random()
            a.put(key, v)
            b.put(key, v)
