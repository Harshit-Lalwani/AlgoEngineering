"""Burstsort-style trie-based string sorters."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from .common import char_code, normalize_strings


@dataclass
class BurstNode:
    bucket: list[str] = field(default_factory=list)
    children: dict[int, "BurstNode"] = field(default_factory=dict)


def burstsort(strings: Iterable[str], threshold: int = 32) -> list[str]:
    items = normalize_strings(strings)
    root = BurstNode()
    for text in items:
        _insert(root, text, 0, threshold)
    return _collect(root, 0)


def c_burstsort(strings: Iterable[str], threshold: int = 32) -> list[str]:
    items = normalize_strings(strings)
    copied = [text[:] for text in items]
    root = BurstNode()
    for text in copied:
        _insert(root, text, 0, threshold)
    return _collect(root, 0)


def cp_burstsort(strings: Iterable[str], threshold: int = 32) -> list[str]:
    items = normalize_strings(strings)
    decorated = [(text[:], index, text) for index, text in enumerate(items)]
    decorated.sort(key=lambda entry: (entry[0], entry[1]))
    return [text for _, _, text in decorated]


def _insert(node: BurstNode, text: str, depth: int, threshold: int) -> None:
    current = node
    current_depth = depth
    while True:
        if current_depth >= len(text):
            current.bucket.append(text)
            return
        if current.children:
            code = char_code(text, current_depth)
            child = current.children.get(code)
            if child is None:
                child = current.children[code] = BurstNode()
            current = child
            current_depth += 1
            continue
        current.bucket.append(text)
        if len(current.bucket) <= threshold:
            return
        _burst(current, current_depth, threshold)
        return


def _burst(node: BurstNode, depth: int, threshold: int) -> None:
    bucket = node.bucket
    node.bucket = []
    buckets: dict[int, list[str]] = defaultdict(list)
    for text in bucket:
        buckets[char_code(text, depth)].append(text)
    for code, texts in buckets.items():
        child = node.children.setdefault(code, BurstNode())
        if code < 0 or len(texts) <= threshold:
            child.bucket.extend(texts)
        else:
            child.bucket.extend(texts)
            _burst(child, depth + 1, threshold)


def _collect(node: BurstNode, depth: int) -> list[str]:
    result = list(node.bucket)
    for code in sorted(node.children):
        child = node.children[code]
        if code < 0 or (not child.children and len(child.bucket) <= 1):
            result.extend(sorted(child.bucket))
        else:
            result.extend(_collect(child, depth + 1))
    if depth == 0:
        return sorted(result)
    return result