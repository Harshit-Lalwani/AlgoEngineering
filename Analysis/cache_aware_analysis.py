"""
Cache-Aware String Sorting — Analysis Script
============================================
Runs after `./build/benchmark` has produced:
  results.csv              (raw per-seed results)
  results_aggregated.csv   (mean ± std across seeds)
  radix_depth.csv          (MSD radix recursion depth by dataset)

Outputs all figures to Analysis/figures/.
Requires: pandas, matplotlib, numpy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

FIGDIR = "figures"
os.makedirs(FIGDIR, exist_ok=True)

ALGO_COLORS = {
    "std::sort":          "#4878CF",
    "multikey_quicksort": "#6ACC65",
    "burstsort":          "#D65F5F",
    "c_burstsort":        "#B47CC7",
    "msd_radix_sort":     "#C4AD66",
    "merge_sort":         "#77BEDB",
    "lazy_funnelsort":    "#F28E2B",
}

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
agg = pd.read_csv("results_aggregated.csv")
raw = pd.read_csv("results.csv")

datasets = ["random", "prefix_heavy", "wiki_random", "wiki_heavy"]
algorithms = list(ALGO_COLORS.keys())

# ---------------------------------------------------------------------------
# Figure 1: Wall-clock time vs N  (with ±1σ error bands)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=False)
axes = axes.flatten()

for ax_i, ds in enumerate(datasets):
    ax = axes[ax_i]
    sub = agg[agg["dataset"] == ds].sort_values("count")
    for algo in algorithms:
        s = sub[sub["algorithm"] == algo]
        if s.empty:
            continue
        color = ALGO_COLORS.get(algo, "gray")
        ax.plot(s["count"], s["elapsed_mean_s"], label=algo,
                color=color, marker="o", linewidth=1.8)
        ax.fill_between(s["count"],
                        s["elapsed_mean_s"] - s["elapsed_std_s"],
                        s["elapsed_mean_s"] + s["elapsed_std_s"],
                        color=color, alpha=0.15)
    ax.set_title(f"{ds}", fontsize=11)
    ax.set_xlabel("N (strings)")
    ax.set_ylabel("Time (s)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

fig.suptitle("Wall-Clock Sorting Time vs N  (mean ± 1σ, 10 seeds)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{FIGDIR}/time_vs_n_all_datasets.png", dpi=150)
plt.close(fig)
print("Saved: time_vs_n_all_datasets.png")

# ---------------------------------------------------------------------------
# Figure 2: Log-log scaling plots (to measure empirical exponent)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for ax_i, ds in enumerate(datasets):
    ax = axes[ax_i]
    sub = agg[agg["dataset"] == ds].sort_values("count")
    for algo in algorithms:
        s = sub[sub["algorithm"] == algo]
        if s.empty() if hasattr(s, 'empty') and callable(s.empty) else s.empty:
            continue
        if len(s) < 2:
            continue
        color = ALGO_COLORS.get(algo, "gray")
        xs = np.log10(s["count"].values)
        ys = np.log10(s["elapsed_mean_s"].values)
        ax.plot(xs, ys, label=algo, color=color, marker="o", linewidth=1.8)
        # Fit linear slope = empirical scaling exponent
        if len(xs) >= 2:
            slope = np.polyfit(xs, ys, 1)[0]
            ax.annotate(f"α={slope:.2f}",
                        xy=(xs[-1], ys[-1]),
                        xytext=(4, 2), textcoords="offset points",
                        fontsize=7, color=color)
    ax.set_title(f"{ds} — log-log scaling", fontsize=11)
    ax.set_xlabel("log₁₀(N)")
    ax.set_ylabel("log₁₀(time / s)")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

fig.suptitle("Log-Log Scaling (slope α = empirical complexity exponent)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{FIGDIR}/loglog_scaling.png", dpi=150)
plt.close(fig)
print("Saved: loglog_scaling.png")

# ---------------------------------------------------------------------------
# Figure 3: Per-character normalised time — fair cross-dataset comparison
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, len(algorithms), figsize=(16, 5), sharey=False)

for ax_i, algo in enumerate(algorithms):
    ax = axes[ax_i]
    sub = agg[agg["algorithm"] == algo]
    for ds in datasets:
        s = sub[sub["dataset"] == ds].sort_values("count")
        if s.empty:
            continue
        ax.plot(s["count"], s["time_per_char_us_mean"],
                label=ds, marker="o", linewidth=1.5)
    ax.set_title(algo, fontsize=9)
    ax.set_xlabel("N")
    ax.set_ylabel("μs per character")
    ax.legend(fontsize=7)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x/1e3):.0f}K"))
    ax.grid(True, alpha=0.3)

fig.suptitle("Time per Character (μs) — Normalised for fair cross-dataset comparison",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{FIGDIR}/time_per_char_normalised.png", dpi=150)
plt.close(fig)
print("Saved: time_per_char_normalised.png")

# ---------------------------------------------------------------------------
# Figure 4: MSD Radix Recursion Depth — the key anomaly
# ---------------------------------------------------------------------------
try:
    depth_df = pd.read_csv("radix_depth.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    for ds in depth_df["dataset"].unique():
        sub = depth_df[depth_df["dataset"] == ds].sort_values("count")
        ax.plot(sub["count"], sub["mean_recursion_depth"],
                marker="o", label=ds, linewidth=2)
    ax.set_xlabel("N (strings)")
    ax.set_ylabel("Mean recursion depth")
    ax.set_title("MSD Radix Sort — Mean Recursion Depth by Dataset\n"
                 "Higher depth = more L2/LLC misses, explains wiki_heavy slowdown")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/radix_recursion_depth.png", dpi=150)
    plt.close(fig)
    print("Saved: radix_recursion_depth.png")
except FileNotFoundError:
    print("radix_depth.csv not found — skipping depth plot (run full benchmark first)")

# ---------------------------------------------------------------------------
# Figure 5: Dataset comparison at fixed N=1M — bar chart
# ---------------------------------------------------------------------------
fixed_n = 1_000_000
if fixed_n in agg["count"].values:
    sub = agg[agg["count"] == fixed_n]
    pivot = sub.pivot(index="algorithm", columns="dataset", values="elapsed_mean_s")
    pivot_std = sub.pivot(index="algorithm", columns="dataset", values="elapsed_std_s")
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(pivot.index))
    w = 0.18
    for i, ds in enumerate(datasets):
        if ds not in pivot.columns:
            continue
        vals = pivot[ds].values
        errs = pivot_std[ds].values if ds in pivot_std.columns else None
        ax.bar(x + i * w, vals, w, label=ds, yerr=errs,
               capsize=3, error_kw={"linewidth": 0.8})
    ax.set_xticks(x + 1.5 * w)
    ax.set_xticklabels(pivot.index, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Time (s)")
    ax.set_title(f"Algorithm Performance by Dataset Type at N={fixed_n:,}\n"
                 f"(mean ± 1σ, 10 seeds)")
    ax.legend(title="Dataset", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/time_vs_dataset_type_N1M.png", dpi=150)
    plt.close(fig)
    print("Saved: time_vs_dataset_type_N1M.png")
else:
    print(f"N={fixed_n:,} not found in aggregated data — skipping bar chart")

print("\nAll figures written to", FIGDIR)
