import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

FIGDIR = "Analysis/figures"
os.makedirs(FIGDIR, exist_ok=True)

# 1. Bar graph for Figure 6 (LLC misses per element)
try:
    df_cache = pd.read_csv("Analysis/cache_profile.csv")
    N = 10000
    df_cache["llc_misses_per_element"] = df_cache["lld_misses"] / N
    
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.bar(df_cache["algorithm"], df_cache["llc_misses_per_element"], color="#B47CC7")
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("LLC Misses per Element")
    ax.set_title(f"LLC Misses per Element at N={N:,} (wiki_random)")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/llc_bar_fixed_n.png", dpi=150)
    plt.close(fig)
    print("Generated llc_bar_fixed_n.png")
except Exception as e:
    print("Error generating Figure 6:", e)

# 2. Line graph for Figure 5 (radix_depth_vs_time.csv)
try:
    df_radix = pd.read_csv("Analysis/radix_depth_vs_time.csv")
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    
    # Remove random dataset
    df_radix = df_radix[df_radix["dataset"] != "random"]
    
    DATASET_COLORS = {
        "prefix_heavy": "#D65F5F",
        "wiki_random": "#6ACC65",
        "wiki_heavy": "#B47CC7",
    }
    
    for ds in sorted(df_radix["dataset"].unique()):
        s = df_radix[df_radix["dataset"] == ds].sort_values("mean_recursion_depth")
        ax.plot(s["mean_recursion_depth"], s["time_per_char_us_mean"], marker='o', 
                label=ds, color=DATASET_COLORS.get(ds, None), linewidth=2)
        for _, r in s.iterrows():
            ax.annotate(f"N={int(r['count']):,}", (r["mean_recursion_depth"], r["time_per_char_us_mean"]), textcoords="offset points", xytext=(5, 4), fontsize=8)

    ax.set_xlabel("Mean recursion depth")
    ax.set_ylabel("μs / char (MSD radix)")
    ax.set_title("MSD radix: recursion depth vs time per character")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/radix_depth_vs_time_per_char_line.png", dpi=150)
    plt.close(fig)
    print("Generated radix_depth_vs_time_per_char_line.png")
except Exception as e:
    print("Error generating Figure 5:", e)

