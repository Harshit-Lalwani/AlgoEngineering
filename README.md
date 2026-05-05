# AlgoEngineering — Cache-Aware & Cache-Oblivious String Sorting

This project implements, benchmarks, and analyses both **cache-aware** (Burstsort, C-Burstsort, MSD Radix Sort) and **cache-oblivious** (K-way Funnelsort, baseline Merge Sort) algorithms for sorting large sets of strings.

---

## Repository Structure

```
.
├── cpp/
│   └── src/
│       ├── algorithms/         # All algorithm implementations
│       │   ├── baselines.{cpp,hpp}        std::sort, multikey quicksort
│       │   ├── burstsort.{cpp,hpp}        cache-aware: Burstsort + C-Burstsort
│       │   ├── radix.{cpp,hpp}            cache-aware: MSD Radix Sort
│       │   └── cache_oblivious.{cpp,hpp}  cache-oblivious: K-way Funnelsort + 2-way merge
│       └── benchmark/
│           └── main.cpp            Benchmark runner (10 seeds, warmup, stats)
├── data/
│   └── dataset_wiki.txt        Wikipedia titles (download via download_data.py)
├── Analysis/
│   ├── results.csv                  Raw per-seed benchmark results
│   ├── results_aggregated.csv       Mean ± std over 10 seeds (primary analysis data)
│   ├── radix_depth.csv              MSD Radix recursion depth by dataset
│   ├── cache_results.csv            Cache miss counts (multi-N, from run_perf.sh)
│   ├── cache_aware_analysis.py      ← Run this to regenerate all figures
│   ├── cache_profile_analysis.py    ← Run after run_perf.sh
│   ├── run_perf.sh                  Shell script: collect cache misses via perf/valgrind
│   └── figures/                     All output plots
```

---

## Build

```bash
# Requires: g++ >= 11, CMake >= 3.16
cd cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

Binary: `cpp/build/benchmark`

---

## Data Download

```bash
python3 download_data.py
```

This writes `data/dataset_wiki.txt` (Wikipedia page titles).

---

## Run Benchmarks

### Full benchmark (10 seeds × 3 sizes × 7 algorithms × 4 datasets)

```bash
cd cpp/build
./benchmark
```

Outputs:
- `Analysis/results.csv` — raw per-seed results
- `Analysis/results_aggregated.csv` — mean ± σ over 10 seeds
- `Analysis/radix_depth.csv` — MSD recursion depth by dataset

### Single-algorithm cache-profiling mode (reduced N for Valgrind)

```bash
./benchmark lazy_funnelsort random
./benchmark msd_radix_sort wiki_heavy
```

---

## Cache Profiling (requires `perf` or `valgrind`)

```bash
cd cpp/build
chmod +x ../../Analysis/run_perf.sh
../../Analysis/run_perf.sh
```

This collects L1 and LLC miss counts at N = {10k, 100k, 1M} and writes `Analysis/cache_results.csv`.

> **Note on Valgrind mode:** cachegrind simulates a simplified cache model. For real PMU counters use `perf stat` on bare metal (Linux). Container/cloud environments often block `perf_event_open`.

---

## Generate Figures

```bash
cd Analysis
pip install pandas matplotlib numpy   # if not already installed
python3 cache_aware_analysis.py       # timing + log-log + depth + per-char plots
python3 cache_profile_analysis.py     # cache miss rate vs N  (requires multi-N cache_results.csv)
```

Figures are written to `Analysis/figures/`.

| Figure | Description |
|---|---|
| `time_vs_n_all_datasets.png` | Wall-clock time vs N with ±1σ shaded ribbon |
| `loglog_scaling.png` | Log-log plot with empirical exponent α annotated |
| `time_per_char_normalised.png` | Time per character (μs) for fair cross-dataset comparison |
| `radix_recursion_depth.png` | MSD radix mean recursion depth — explains wiki_heavy slowdown |
| `time_vs_dataset_type_N1M.png` | Bar chart at N=1M with error bars |
| `l1_miss_rate_vs_n.png` | L1 miss rate vs N (needs multi-N cache run) |
| `llc_miss_rate_vs_n.png` | LLC miss rate vs N (needs multi-N cache run) |

---

## Algorithms

| Algorithm | File | Class | I/O Complexity |
|---|---|---|---|
| `std::sort` | `baselines.cpp` | Baseline | O((N/B) log N) |
| `multikey_quicksort` | `baselines.cpp` | Baseline | O(N · D / B) expected |
| `burstsort` | `burstsort.cpp` | Cache-aware | O(N · D / B) |
| `c_burstsort` | `burstsort.cpp` | Cache-aware | O(N · D / B), lower constant |
| `msd_radix_sort` | `radix.cpp` | Cache-aware | O(N · D / B), degrades when alphabet ≥ M/B |
| `merge_sort` | `cache_oblivious.cpp` | Oblivious baseline | O((N/B) log₂(N/B)) |
| `lazy_funnelsort` | `cache_oblivious.cpp` | Cache-oblivious | O((N/B) log_{M/B}(N/B)) |

where D = mean distinguishing prefix length, B = cache line size, M = cache size.

---

## Hardware / Environment

Record your machine specs in the report. The benchmark does **not** pin to a CPU core; for publication-quality results, pin via `taskset -c 0 ./benchmark` on Linux and disable CPU frequency scaling:

```bash
sudo cpupower frequency-set --governor performance
taskset -c 0 ./benchmark
```
