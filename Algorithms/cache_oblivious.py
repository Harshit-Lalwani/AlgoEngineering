"""Cache-oblivious style comparison-based and signature-based sorters."""

from __future__ import annotations

from heapq import merge
from typing import Iterable

from .common import normalize_strings, prefix_key


def external_signature_sort(strings: Iterable[str], signature_length: int = 8, run_size: int = 1024) -> list[str]:
    items = normalize_strings(strings)
    if len(items) <= run_size:
        return sorted(items, key=lambda text: (prefix_key(text, signature_length), text))

    runs = []
    for start in range(0, len(items), run_size):
        chunk = items[start : start + run_size]
        chunk.sort(key=lambda text: (prefix_key(text, signature_length), text))
        runs.append(chunk)

    merged = list(merge(*runs, key=lambda text: (prefix_key(text, signature_length), text)))
    merged.sort()
    return merged


def lazy_funnelsort(strings: Iterable[str], fanout: int = 8) -> list[str]:
    items = normalize_strings(strings)
    if len(items) <= 1:
        return items
    return _lazy_funnelsort(items, fanout)


def _lazy_funnelsort(items: list[str], fanout: int) -> list[str]:
    if len(items) <= fanout:
        return sorted(items)

    runs = []
    for start in range(0, len(items), fanout):
        runs.append(_lazy_funnelsort(items[start : start + fanout], fanout))

    return list(merge(*runs))