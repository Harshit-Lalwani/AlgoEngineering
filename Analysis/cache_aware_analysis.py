"""
Extended cache-aware analysis script.

This script is intended as a temporary drop-in replacement / extension for
Analysis/cache_aware_analysis.py.

Inputs expected in the current working directory (typically repo/Analysis):
- results.csv
- results_aggregated.csv
- radix_depth.csv (optional but recommended)
- cache_results.csv (optional; only used for cache-related joins if present)

Outputs:
- figures/*.png
- summary_best_at_largest_n.csv
- dataset_time_per_char_fixed_n.csv
- radix_depth_vs_time.csv
- miss_rate_two_algo.csv (if cache_results.csv available)
"""

import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

FIGDIR = "figures"
os.makedirs(FIGDIR, exist_ok=True)

ALGO_COLORS = {
    "std::sort": "#4878CF",
    "multikey_quicksort": "#6ACC65",
    "burstsort": "#D65F5F",
    "c_burstsort": "#B47CC7",
    "msd_radix_sort": "#C4AD66",
    "merge_sort": "#77BEDB",
    "lazy_funnelsort": "#F28E2B",
}

DATASET_COLORS = {
    "random": "#4878CF",
    "prefix_heavy": "#D65F5F",
    "wiki_random": "#6ACC65",
    "wiki_heavy": "#B47CC7",
}


def fmt_int(x, _):
    try:
        return f"{int(x):,}"
    except Exception:
        return str(x)


def load_csv(path, required=True):
    if os.path.exists(path):
        return pd.read_csv(path)
    if required:
        raise FileNotFoundError(path)
    return None


agg = load_csv("results_aggregated.csv")
raw = load_csv("results.csv", required=False)
depth_df = load_csv("radix_depth.csv", required=False)
cache_df = load_csv("cache_results.csv", required=False)

# Normalize expected columns
if "elapsed_mean_s" not in agg.columns and "elapsed_mean" in agg.columns:
    agg = agg.rename(columns={"elapsed_mean": "elapsed_mean_s"})
if "elapsed_std_s" not in agg.columns and "elapsed_std" in agg.columns:
    agg = agg.rename(columns={"elapsed_std": "elapsed_std_s"})
if "time_per_char_us_mean" not in agg.columns and "time_per_char_us" in agg.columns:
    agg = agg.rename(columns={"time_per_char_us": "time_per_char_us_mean"})
if "time_per_element_us_mean" not in agg.columns and "time_per_element_us" in agg.columns:
    agg = agg.rename(columns={"time_per_element_us": "time_per_element_us_mean"})

# Guardrails
required_cols = {"algorithm", "dataset", "count", "elapsed_mean_s"}
missing = required_cols - set(agg.columns)
if missing:
    raise ValueError(f"results_aggregated.csv missing columns: {sorted(missing)}")

# Fill std with zero if absent
if "elapsed_std_s" not in agg.columns:
    agg["elapsed_std_s"] = 0.0

# -------------------------
# Addition 1: best-at-largest-N summary + plot
# -------------------------
largest_n = int(agg["count"].max())
sub_largest = agg[agg["count"] == largest_n].copy()
summary_rows = []
for ds in sorted(sub_largest["dataset"].unique()):
    ds_df = sub_largest[sub_largest["dataset"] == ds].sort_values("elapsed_mean_s")
    if ds_df.empty:
        continue
    best = ds_df.iloc[0]
    second = ds_df.iloc[1] if len(ds_df) > 1 else None
    speedup_vs_second = (second["elapsed_mean_s"] / best["elapsed_mean_s"]) if second is not None and best["elapsed_mean_s"] > 0 else np.nan
    summary_rows.append({
        "dataset": ds,
        "largest_n": largest_n,
        "best_algorithm": best["algorithm"],
        "best_time_s": best["elapsed_mean_s"],
        "best_std_s": best.get("elapsed_std_s", 0.0),
        "runner_up_algorithm": second["algorithm"] if second is not None else "",
        "runner_up_time_s": second["elapsed_mean_s"] if second is not None else np.nan,
        "speedup_vs_runner_up": speedup_vs_second,
    })

summary_best = pd.DataFrame(summary_rows)
summary_best.to_csv("summary_best_at_largest_n.csv", index=False)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()
for i, ds in enumerate(sorted(sub_largest["dataset"].unique())):
    ax = axes[i]
    ds_df = sub_largest[sub_largest["dataset"] == ds].sort_values("elapsed_mean_s")
    colors = [ALGO_COLORS.get(a, "gray") for a in ds_df["algorithm"]]
    ax.bar(ds_df["algorithm"], ds_df["elapsed_mean_s"], yerr=ds_df["elapsed_std_s"], color=colors, capsize=3)
    ax.set_title(f"{ds} @ N={largest_n:,}")
    ax.set_ylabel("Time (s)")
    ax.tick_params(axis='x', rotation=25)
    ax.grid(axis="y", alpha=0.3)
fig.suptitle("Best algorithm by dataset at largest N (mean ± 1σ)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{FIGDIR}/best_algorithm_largest_n.png", dpi=150)
plt.close(fig)

# -------------------------
# Addition 2: time-vs-N with log-x for selected dataset(s)
# -------------------------
for focus_ds in [d for d in ["wiki_random", "random"] if d in agg["dataset"].unique()]:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ds = agg[agg["dataset"] == focus_ds].sort_values("count")
    for algo in sorted(ds["algorithm"].unique()):
        s = ds[ds["algorithm"] == algo].sort_values("count")
        if s.empty:
            continue
        color = ALGO_COLORS.get(algo, "gray")
        ax.plot(s["count"], s["elapsed_mean_s"], marker='o', linewidth=1.8, label=algo, color=color)
        ax.fill_between(s["count"], s["elapsed_mean_s"] - s["elapsed_std_s"], s["elapsed_mean_s"] + s["elapsed_std_s"], color=color, alpha=0.15)
    ax.set_xscale("log")
    ax.set_xlabel("N (log scale)")
    ax.set_ylabel("Time (s)")
    ax.set_title(f"Time vs N (log-x) on {focus_ds}")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_int))
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/time_vs_n_logx_{focus_ds}.png", dpi=150)
    plt.close(fig)

# -------------------------
# Addition 3: time-per-character vs dataset at fixed N, with CSV
# -------------------------
if "time_per_char_us_mean" in agg.columns:
    # Prefer N=1e6, else median available count
    preferred_n = 1_000_000
    unique_counts = sorted(agg["count"].unique())
    fixed_n = preferred_n if preferred_n in set(unique_counts) else int(unique_counts[len(unique_counts) // 2])
    fixed = agg[agg["count"] == fixed_n].copy()
    out_rows = []
    for _, r in fixed.iterrows():
        out_rows.append({
            "count": fixed_n,
            "algorithm": r["algorithm"],
            "dataset": r["dataset"],
            "time_per_char_us_mean": r["time_per_char_us_mean"],
            "elapsed_mean_s": r["elapsed_mean_s"],
        })
    tpc_df = pd.DataFrame(out_rows)
    tpc_df.to_csv("dataset_time_per_char_fixed_n.csv", index=False)

    algos = sorted(fixed["algorithm"].unique())
    ncols = 3
    nrows = math.ceil(len(algos) / ncols) or 1
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 4.5 * nrows), squeeze=False)
    axes = axes.flatten()
    for i, algo in enumerate(algos):
        ax = axes[i]
        s = fixed[fixed["algorithm"] == algo].copy()
        s = s.sort_values("dataset")
        colors = [DATASET_COLORS.get(d, "gray") for d in s["dataset"]]
        ax.bar(s["dataset"], s["time_per_char_us_mean"], color=colors)
        ax.set_title(f"{algo} @ N={fixed_n:,}")
        ax.set_ylabel("μs / char")
        ax.tick_params(axis='x', rotation=20)
        ax.grid(axis="y", alpha=0.3)
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    fig.suptitle("Time per character across datasets at fixed N", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/time_per_char_vs_dataset_fixed_n.png", dpi=150)
    plt.close(fig)

# -------------------------
# Addition 4: radix depth vs time-per-char scatter + CSV
# -------------------------
if depth_df is not None and "time_per_char_us_mean" in agg.columns:
    if "mean_recursion_depth" not in depth_df.columns:
        # try a couple of common column names; else skip
        for cand in ["avg_depth", "mean_depth"]:
            if cand in depth_df.columns:
                depth_df = depth_df.rename(columns={cand: "mean_recursion_depth"})
                break
    if "mean_recursion_depth" in depth_df.columns:
        radix_t = agg[agg["algorithm"] == "msd_radix_sort"][["dataset", "count", "time_per_char_us_mean", "elapsed_mean_s"]].copy()
        merged = depth_df.merge(radix_t, on=["dataset", "count"], how="inner")
        merged.to_csv("radix_depth_vs_time.csv", index=False)
        if not merged.empty:
            fig, ax = plt.subplots(figsize=(8.5, 5.5))
            for ds in sorted(merged["dataset"].unique()):
                s = merged[merged["dataset"] == ds]
                ax.scatter(s["mean_recursion_depth"], s["time_per_char_us_mean"], s=70, label=ds, color=DATASET_COLORS.get(ds, None))
                for _, r in s.iterrows():
                    ax.annotate(f"N={int(r['count']):,}", (r["mean_recursion_depth"], r["time_per_char_us_mean"]), textcoords="offset points", xytext=(5, 4), fontsize=8)
            ax.set_xlabel("Mean recursion depth")
            ax.set_ylabel("μs / char (MSD radix)")
            ax.set_title("MSD radix: recursion depth vs time per character")
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            fig.savefig(f"{FIGDIR}/radix_depth_vs_time_per_char.png", dpi=150)
            plt.close(fig)

# -------------------------
# Addition 5: if cache data exists, compare two key algorithms only
# -------------------------
if cache_df is not None:
    c = cache_df.copy()
    if "N" not in c.columns and "count" in c.columns:
        c = c.rename(columns={"count": "N"})
    if "l1_miss_rate" not in c.columns:
        if {"l1_misses", "l1_refs"}.issubset(c.columns):
            c["l1_miss_rate"] = c["l1_misses"] / c["l1_refs"].replace(0, np.nan)
        elif {"d1_misses", "d_refs"}.issubset(c.columns):
            c["l1_miss_rate"] = c["d1_misses"] / c["d_refs"].replace(0, np.nan)
    if "llc_miss_rate" not in c.columns:
        if {"llc_misses", "llc_refs"}.issubset(c.columns):
            c["llc_miss_rate"] = c["llc_misses"] / c["llc_refs"].replace(0, np.nan)
        elif {"lld_misses", "d_refs"}.issubset(c.columns):
            c["llc_miss_rate"] = c["lld_misses"] / c["d_refs"].replace(0, np.nan)

    keep_algos = [a for a in ["std::sort", "c_burstsort"] if a in set(c.get("algorithm", []))]
    if keep_algos and "N" in c.columns:
        miss_rows = c[c["algorithm"].isin(keep_algos)].copy()
        cols_to_write = [col for col in ["algorithm", "dataset", "N", "l1_miss_rate", "llc_miss_rate"] if col in miss_rows.columns]
        if cols_to_write:
            miss_rows[cols_to_write].to_csv("miss_rate_two_algo.csv", index=False)

        for metric, title, fname in [
            ("l1_miss_rate", "L1 miss rate vs N", "two_algo_l1_miss_rate_vs_n.png"),
            ("llc_miss_rate", "LLC miss rate vs N", "two_algo_llc_miss_rate_vs_n.png"),
        ]:
            if metric not in miss_rows.columns or miss_rows[metric].notna().sum() == 0:
                continue
            focus_ds = "wiki_random" if "dataset" in miss_rows.columns and "wiki_random" in set(miss_rows.get("dataset", [])) else miss_rows["dataset"].dropna().iloc[0] if "dataset" in miss_rows.columns and not miss_rows["dataset"].dropna().empty else None
            plot_df = miss_rows[miss_rows["dataset"] == focus_ds] if focus_ds is not None and "dataset" in miss_rows.columns else miss_rows
            fig, ax = plt.subplots(figsize=(8.5, 5.2))
            for algo in keep_algos:
                s = plot_df[plot_df["algorithm"] == algo].sort_values("N")
                if s.empty:
                    continue
                ax.plot(s["N"], s[metric], marker='o', linewidth=2, label=algo, color=ALGO_COLORS.get(algo, None))
            ax.set_xlabel("N")
            ax.set_ylabel(metric.replace("_", " "))
            if focus_ds:
                ax.set_title(f"{title} on {focus_ds}")
            else:
                ax.set_title(title)
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_int))
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            ax.figure.savefig(f"{FIGDIR}/{fname}", dpi=150)
            plt.close(fig)

if __name__ == "__main__":
    print("Extended analysis complete.")
    print("Generated CSVs:")
    for f in [
        "summary_best_at_largest_n.csv",
        "dataset_time_per_char_fixed_n.csv",
        "radix_depth_vs_time.csv",
        "miss_rate_two_algo.csv",
    ]:
        if os.path.exists(f):
            print(" -", f)
    print("Generated figures under figures/")
