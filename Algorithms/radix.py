"""Radix-style string sorters."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .common import char_code, normalize_strings, prefix_key


def msd_radix_sort(strings: Iterable[str]) -> list[str]:
    items = normalize_strings(strings)
    return _msd_sort(items, 0)


def cradix_sort(strings: Iterable[str], prefix_length: int = 8) -> list[str]:
    items = normalize_strings(strings)
    decorated = [(prefix_key(text, prefix_length), text) for text in items]
    decorated.sort(key=lambda pair: (pair[0], pair[1]))
    return [text for _, text in decorated]


def _msd_sort(items: list[str], depth: int) -> list[str]:
    if len(items) <= 1:
        return items

    buckets: dict[int, list[str]] = defaultdict(list)
    for text in items:
        buckets[char_code(text, depth)].append(text)

    ordered_keys = sorted(buckets)
    result: list[str] = []
    for key in ordered_keys:
        bucket = buckets[key]
        if key < 0 or len(bucket) <= 1:
            result.extend(bucket)
        else:
            result.extend(_msd_sort(bucket, depth + 1))
    return result