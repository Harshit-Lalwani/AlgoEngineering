"""Baseline string sorters used in the comparisons."""

from __future__ import annotations

from typing import Iterable

from .common import char_code, normalize_strings


def python_sort(strings: Iterable[str]) -> list[str]:
    items = normalize_strings(strings)
    items.sort()
    return items


def multikey_quicksort(strings: Iterable[str]) -> list[str]:
    items = normalize_strings(strings)
    if len(items) <= 1:
        return items
    _multikey_quicksort(items, 0, len(items), 0)
    return items


def _multikey_quicksort(items: list[str], left: int, right: int, depth: int) -> None:
    if right - left <= 1:
        return

    pivot = char_code(items[(left + right) // 2], depth)
    lt = left
    i = left
    gt = right - 1

    while i <= gt:
        current = char_code(items[i], depth)
        if current < pivot:
            items[lt], items[i] = items[i], items[lt]
            lt += 1
            i += 1
        elif current > pivot:
            items[i], items[gt] = items[gt], items[i]
            gt -= 1
        else:
            i += 1

    _multikey_quicksort(items, left, lt, depth)
    if pivot >= 0:
        _multikey_quicksort(items, lt, gt + 1, depth + 1)
    _multikey_quicksort(items, gt + 1, right, depth)