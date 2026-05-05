# Project Expansion To-Do List

Based on the algorithm engineering literature critique, here is the roadmap to elevate the project's rigor and depth.

## Phase 1: Local Implementation (Feasible Immediately)
- [ ] **Scale up to 1M+ strings:** Add larger dataset sizes (e.g., `1,000,000`) to the benchmarking suite for runtime analysis to observe the critical crossover point where burstsort begins to dominate.
- [x] **Real-world Datasets:** Write an ingest script to download and use real-world corpuses (e.g., Project Gutenberg dictionary, Wikipedia titles, web URLs) which have vastly different prefix distributions than synthetic data.
- [x] **Implement C-Burstsort:** Write a C++ variant of burstsort that copies string characters directly into contiguous `char` arrays, demonstrating the spatial-locality improvement over arrays of string pointers.
- [ ] **Throughput Metrics & Scaling Plots:** Calculate sorting throughput (MB/s) and update the Jupyter notebooks to include log-log plots of Wall-clock Time vs. N (to demonstrate empirical $O(N \log N)$ scaling).
- [ ] **Parameter Sweeps:**
    - Sweep string lengths and alphabet sizes in the data generator.
    - Sweep Burstsort bucket thresholds (e.g., from 512 bytes to 32KB) to empirically find the optimal cache-line fit point.
- [ ] **Statistical Rigor:** Increase the number of runs/seeds in `main.cpp` (e.g., to 10) and report the mean ± standard deviation.
- [ ] **LCP Analysis:** Calculate and plot the Longest Common Prefix (LCP) distribution for the datasets to theoretically ground the complexity.

## Phase 2: Cluster / Colab Execution (Requires Bare-Metal Access)
- [ ] **Hardware Counters via `perf stat`:** Write a shell script (`run_perf.sh`) to capture real hardware Performance Monitoring Unit (PMU) counters such as `L1-dcache-load-misses`, `LLC-load-misses`, and `dTLB-load-misses`. Run this externally to bypass local container limitations.
- [ ] **Peak Memory Tracking:** Incorporate `/usr/bin/time -v` or Valgrind's `massif` into the cluster bash script to record peak heap usage (Max resident set size), properly documenting the memory vs. speed tradeoff of copy-based algorithms.
