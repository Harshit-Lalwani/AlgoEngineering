"""Shared helpers for string sorting implementations."""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def normalize_strings(strings: Iterable[str]) -> list[str]:
    return [str(item) for item in strings]


def char_code(text: str, depth: int) -> int:
    if depth >= len(text):
        return -1
    return ord(text[depth])


def prefix_key(text: str, length: int) -> str:
    if length <= 0:
        return ""
    return text[:length]


def lcp_length(left: str, right: str, start: int = 0) -> int:
    index = start
    limit = min(len(left), len(right))
    while index < limit and left[index] == right[index]:
        index += 1
    return index


def is_sorted(strings: Sequence[str]) -> bool:
    return all(strings[index - 1] <= strings[index] for index in range(1, len(strings)))