"""Benchmark helpers and synthetic dataset generators."""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from random import Random
from time import perf_counter
from statistics import mean
from typing import Callable, Iterable

from .common import is_sorted, normalize_strings


SortFunction = Callable[[Iterable[str]], list[str]]


@dataclass(frozen=True)
class BenchmarkResult:
    algorithm: str
    count: int
    total_length: int
    elapsed_seconds: float
    sorted_correctly: bool


def benchmark_sort(name: str, sort_function: SortFunction, strings: Iterable[str]) -> tuple[BenchmarkResult, list[str]]:
    items = normalize_strings(strings)
    start = perf_counter()
    result = sort_function(items)
    elapsed = perf_counter() - start
    benchmark = BenchmarkResult(
        algorithm=name,
        count=len(items),
        total_length=sum(len(text) for text in items),
        elapsed_seconds=elapsed,
        sorted_correctly=is_sorted(result),
    )
    return benchmark, result


def benchmark_suite(
    algorithms: list[tuple[str, SortFunction]],
    dataset_factories: dict[str, Callable[[int, int], list[str]]],
    *,
    sizes: Iterable[int] = (32, 64, 128),
    seeds: Iterable[int] = (0, 1, 2),
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for dataset_name, factory in dataset_factories.items():
        for count in sizes:
            for seed in seeds:
                sample = factory(count, seed)
                expected = sorted(sample)
                for algorithm_name, algorithm in algorithms:
                    benchmark, output = benchmark_sort(algorithm_name, algorithm, sample)
                    if output != expected:
                        raise AssertionError(f"{algorithm_name} produced an incorrect ordering for {dataset_name}")
                    rows.append(
                        {
                            "dataset": dataset_name,
                            "count": count,
                            "seed": seed,
                            "algorithm": benchmark.algorithm,
                            "elapsed_seconds": benchmark.elapsed_seconds,
                            "sorted_correctly": benchmark.sorted_correctly,
                            "total_length": benchmark.total_length,
                        }
                    )
    return rows


def summarize_benchmarks(rows: Iterable[dict[str, object]], group_key: str = "algorithm") -> list[dict[str, object]]:
    grouped: dict[object, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[row[group_key]].append(row)

    summaries: list[dict[str, object]] = []
    for key in sorted(grouped, key=str):
        items = grouped[key]
        elapsed_values = [float(item["elapsed_seconds"]) for item in items]
        summaries.append(
            {
                group_key: key,
                "runs": len(items),
                "mean_elapsed_seconds": mean(elapsed_values),
                "min_elapsed_seconds": min(elapsed_values),
                "max_elapsed_seconds": max(elapsed_values),
                "all_sorted_correctly": all(bool(item["sorted_correctly"]) for item in items),
            }
        )
    return summaries


def generate_dataset(
    *,
    count: int,
    min_length: int = 4,
    max_length: int = 24,
    alphabet: str = "abcdefghijklmnopqrstuvwxyz",
    shared_prefix: str = "",
    seed: int = 0,
) -> list[str]:
    rng = Random(seed)
    dataset: list[str] = []
    for _ in range(count):
        length = rng.randint(min_length, max_length)
        suffix_length = max(0, length - len(shared_prefix))
        suffix = "".join(rng.choice(alphabet) for _ in range(suffix_length))
        dataset.append(shared_prefix + suffix)
    return dataset


def generate_prefix_heavy_dataset(*, count: int, seed: int = 0) -> list[str]:
    rng = Random(seed)
    prefixes = ["al", "cache", "burst", "string", "prefix"]
    dataset: list[str] = []
    for index in range(count):
        prefix = prefixes[index % len(prefixes)]
        tail = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(2, 14)))
        dataset.append(prefix + tail)
    rng.shuffle(dataset)
    return dataset