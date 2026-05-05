"""
Cache Miss Analysis Script
==========================
Expects cache_results.csv to contain data at MULTIPLE sizes
(N = 100k, 1M, 5M).  Run:

    cd cpp/build
    for N in 100000 1000000 5000000; do
        valgrind --tool=cachegrind --I1=32768,8,64 --D1=32768,8,64 \\
                 --LL=8388608,16,64 --cachegrind-out-file=cg.out.$N \\
                 ./benchmark lazy_funnelsort random
        cg_annotate cg.out.$N > cg_annotated.$N.txt
    done

Then parse the L1/LLC miss counts and write them into cache_results.csv.
Column format expected:
    algorithm, dataset, N, l1_misses, l1_refs, llc_misses, llc_refs

Outputs:
    figures/l1_miss_rate_vs_n.png
    figures/llc_miss_rate_vs_n.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

FIGDIR = "figures"
os.makedirs(FIGDIR, exist_ok=True)

try:
    df = pd.read_csv("cache_results.csv")
except FileNotFoundError:
    print("cache_results.csv not found. Run Valgrind/perf at multiple N values first.")
    exit(1)

# Compute miss rates
if "l1_refs" in df.columns and "l1_misses" in df.columns:
    df["l1_miss_rate"] = df["l1_misses"] / df["l1_refs"]
if "llc_refs" in df.columns and "llc_misses" in df.columns:
    df["llc_miss_rate"] = df["llc_misses"] / df["llc_refs"]

# Only valid if we have multiple N values
if df["N"].nunique() < 2:
    print("WARNING: cache_results.csv only has 1 value of N (N=10000).")
    print("Cache behaviour at N=10000 is uninformative — all algorithms fit in L2.")
    print("Re-run Valgrind at N=100000, 1000000, 5000000 to get meaningful plots.")
    exit(0)

for metric, label, fname in [
    ("l1_miss_rate",  "L1 miss rate",  "l1_miss_rate_vs_n.png"),
    ("llc_miss_rate", "LLC miss rate", "llc_miss_rate_vs_n.png"),
]:
    if metric not in df.columns:
        continue
    fig, ax = plt.subplots(figsize=(9, 5))
    for algo in df["algorithm"].unique():
        sub = df[df["algorithm"] == algo].sort_values("N")
        ax.plot(sub["N"], sub[metric], marker="o", label=algo, linewidth=2)
    ax.set_xlabel("N (strings)")
    ax.set_ylabel(label)
    ax.set_title(f"{label} vs N by Algorithm")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/{fname}", dpi=150)
    plt.close(fig)
    print(f"Saved: {fname}")
