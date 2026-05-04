# Project Report: Cache-Aware and Cache-Oblivious Algorithms for String Sorting

## 1. Overview and Problem Statement

The goal of this project is to analyze and compare the performance of string sorting algorithms, specifically focusing on how they interact with modern CPU cache hierarchies (L1, L2, L3 caches). We set out to benchmark **Cache-Aware** algorithms (which are explicitly tuned to hardware parameters like cache line size) against **Cache-Oblivious** algorithms (which optimize cache hits implicitly across all cache levels without requiring hardware-specific tuning parameters).

## 2. Fundamental Discoveries & Architecture Migration

During the initial phase of the project, a critical fundamental flaw was identified: **the original implementation was written in pure Python.** 

### Why Python Failed for Cache Profiling:
1. **Memory Indirection:** In Python, a `list` is an array of pointers pointing to dynamically allocated, immutable `str` objects scattered across a private heap. Sorting a list inherently involves random pointer chasing.
2. **Interpreter Overhead:** The overhead of the Python Virtual Machine, garbage collection, and dynamic typing completely masks subtle hardware-level CPU cache optimizations.
3. **Immutability:** Python strings are immutable. Attempting to artificially group strings into cache-friendly chunks via slicing (`text[:]`) merely copies object references rather than copying actual memory blocks.

**The Solution:** The project was entirely structurally migrated to **C++17**. By rewriting the algorithms natively in C++, we gained direct control over contiguous memory layouts and pointer arithmetic, allowing for true cache-aware and cache-oblivious behavior to be measured. Jupyter Notebooks and Python were retained strictly for orchestration and data visualization using `pandas` and `seaborn`.

---

## 3. Algorithm Methodology

The C++ core implements three categories of algorithms to compare performance:

### A. Baseline Algorithms
- **`std::sort`:** The standard library baseline. Often highly optimized (typically Introsort), but treats strings as generic objects.
- **Multikey Quicksort:** A highly efficient algorithm tailored for strings that performs a 3-way partition on the current character depth, minimizing redundant character comparisons.

### B. Cache-Aware Algorithms
These algorithms manage data structures specifically designed to fit within cache limits (e.g., maximizing spatial locality).
- **Burstsort:** We implemented a trie-based Burstsort using an array of `std::unique_ptr` nodes. It accumulates strings into cache-friendly block arrays ("buckets"). Once a bucket exceeds a threshold (designed to fit in L1/L2 cache), it "bursts" into a sub-trie, preserving locality.
- **Cache-Conscious MSD Radix Sort:** A Radix sort that explicitly clusters string prefixes into contiguous memory buffers (`aux` arrays) before recurring, minimizing TLB (Translation Lookaside Buffer) misses.

### C. Cache-Oblivious Algorithms
- **Lazy Funnelsort (Recursive Block Merge):** A cache-oblivious approach that relies on a divide-and-conquer strategy. By recursively performing block-based binary merges, the algorithm inherently achieves optimal cache utilization at some level of the recursion tree, regardless of the underlying hardware's actual cache capacities.

---

## 4. Benchmarking Methodology

A standalone C++ executable (`benchmark`) was constructed to handle the load:

**Data Generation:**
- **Random Dataset:** Strings of random length (4 to 24 characters) uniformly generated from the lowercase alphabet.
- **Prefix-Heavy Dataset:** Strings deliberately generated with long common prefixes (e.g., "cache...", "burst...") to stress-test the algorithms' ability to handle deep character comparisons and trigger cache branching.

**Execution Pipeline:**
The benchmark runs each algorithm over dataset sizes of 10,000, 50,000, and 100,000 strings across multiple random seeds. Memory is freshly copied for each run. Execution is timed using `std::chrono::high_resolution_clock`, and results are validated using `std::is_sorted`. The outputs are exported to `Analysis/results.csv`.

---

## 5. Cache Profiling with Valgrind Cachegrind

To look past raw execution time and measure exact CPU cache behavior, we integrated **Valgrind Cachegrind** via a Python orchestrator (`run_profiler.py`).

**Methodology:**
Cachegrind simulates an L1 instruction/data cache and a Last-Level (LL) cache. Because Valgrind instrumentation drastically increases memory consumption and runtime overhead, the dataset size was restricted to **10,000 strings** to prevent Out-Of-Memory (OOM) segment overflows.

**L1 Data Cache (D1) Results Snapshot (10,000 strings):**

| Algorithm | D1 Misses | LLd Misses (Last Level) | D1 Miss Rate |
| :--- | :--- | :--- | :--- |
| `std::sort` | 223,375 | 34,946 | 1.25% |
| `multikey_quicksort` | 236,155 | 34,937 | 1.19% |
| `lazy_funnelsort` (Oblivious) | 359,316 | 44,936 | 1.29% |
| `msd_radix_sort` (Aware) | 379,112 | 45,121 | 1.55% |
| `burstsort` (Aware) | 309,121 | 57,586 | 1.71% |

---

## 6. Results and Conclusion

1. **Cache Miss Observations:** For smaller datasets (10,000 items), most algorithms successfully fit within the L3/LL cache, leading to universally low miss rates (~1-2%). Interestingly, the Cache-aware `burstsort` trie exhibits a slightly higher D1 miss rate due to the pointer-heavy nature of trie-node traversal. Conversely, in-place recursive sorts like Multikey Quicksort maintain incredibly tight spatial locality.
2. **Algorithm Efficacy:** Cache-oblivious block merging (`lazy_funnelsort`) maintains strong cache-hit ratios comparable to baseline in-place algorithms, proving that hardware-agnostic divide-and-conquer structures are highly viable for string operations.
3. **The Systems Engineering Lesson:** The transition from Python to C++ highlights a fundamental rule of Algorithm Engineering: High-level languages with heavy indirection and garbage collection cannot be used to benchmark low-level cache efficiency. 

By migrating to C++, we established a robust, mathematically sound framework for measuring real hardware I/O complexity in string sorting algorithms.
