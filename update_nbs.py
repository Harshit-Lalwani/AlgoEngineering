import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    sns.set_theme(style="whitegrid", palette="Set2")
    os.makedirs("Analysis/figures", exist_ok=True)
    
    # Load data
    results_file = "Analysis/results.csv"
    cache_file = "Analysis/cache_results.csv"
    
    if not os.path.exists(results_file) or not os.path.exists(cache_file):
        print("Data files not found.")
        return

    res_df = pd.read_csv(results_file)
    cache_df = pd.read_csv(cache_file)
    
    # Derived metrics
    res_df["time_per_element_us"] = (res_df["elapsed_seconds"] / res_df["count"]) * 1e6
    cache_df["l1_miss_per_element"] = cache_df["d1_misses"] / cache_df["count"]
    cache_df["llc_miss_per_element"] = cache_df["lld_misses"] / cache_df["count"]
    
    # Algorithm colors for consistency
    algos = res_df['algorithm'].unique()
    palette = sns.color_palette("Set2", len(algos))
    color_map = dict(zip(algos, palette))

    # Plot 1: Time per Element vs N (Random dataset)
    plt.figure(figsize=(8, 5))
    df_rand = res_df[res_df["dataset"] == "random"]
    sns.lineplot(data=df_rand, x="count", y="time_per_element_us", hue="algorithm", marker="o", palette=color_map)
    plt.xscale("log")
    plt.title("Execution Time per Element (Random Dataset)")
    plt.xlabel("Number of Strings (N)")
    plt.ylabel("Time per Element (μs)")
    plt.tight_layout()
    plt.savefig("Analysis/figures/time_vs_n_random.png", dpi=300)
    plt.close()

    # Plot 2: Time per Element vs N (Wiki Random dataset)
    plt.figure(figsize=(8, 5))
    df_wiki = res_df[res_df["dataset"] == "wiki_random"]
    sns.lineplot(data=df_wiki, x="count", y="time_per_element_us", hue="algorithm", marker="o", palette=color_map)
    plt.xscale("log")
    plt.title("Execution Time per Element (Wiki Random Dataset)")
    plt.xlabel("Number of Strings (N)")
    plt.ylabel("Time per Element (μs)")
    plt.tight_layout()
    plt.savefig("Analysis/figures/time_vs_n_wiki.png", dpi=300)
    plt.close()

    # Plot 3: LLC Misses per Element vs N (Wiki Random)
    plt.figure(figsize=(8, 5))
    df_cache_wiki = cache_df[cache_df["dataset"] == "wiki_random"]
    sns.lineplot(data=df_cache_wiki, x="count", y="llc_miss_per_element", hue="algorithm", marker="s", palette=color_map)
    plt.xscale("log")
    plt.yscale("log")
    plt.title("LLC Misses per Element (Wiki Random Dataset)")
    plt.xlabel("Number of Strings (N)")
    plt.ylabel("LLC Misses per Element")
    plt.tight_layout()
    plt.savefig("Analysis/figures/llc_vs_n_wiki.png", dpi=300)
    plt.close()

    # Plot 4: L1 Misses per Element vs N (Random)
    plt.figure(figsize=(8, 5))
    df_cache_rand = cache_df[cache_df["dataset"] == "random"]
    sns.lineplot(data=df_cache_rand, x="count", y="l1_miss_per_element", hue="algorithm", marker="s", palette=color_map)
    plt.xscale("log")
    plt.yscale("log")
    plt.title("L1 Misses per Element (Random Dataset)")
    plt.xlabel("Number of Strings (N)")
    plt.ylabel("L1 Misses per Element")
    plt.tight_layout()
    plt.savefig("Analysis/figures/l1_vs_n_random.png", dpi=300)
    plt.close()

    # Plot 5: Bar Chart for N = 5,000,000
    plt.figure(figsize=(10, 6))
    df_large = res_df[res_df["count"] == 5000000]
    sns.barplot(data=df_large, x="dataset", y="time_per_element_us", hue="algorithm", palette=color_map)
    plt.title("Execution Time per Element (N = 5,000,000)")
    plt.xlabel("Dataset")
    plt.ylabel("Time per Element (μs)")
    plt.tight_layout()
    plt.savefig("Analysis/figures/bar_time_large.png", dpi=300)
    plt.close()

    print("Generated plots in Analysis/figures/")

    # Update Notebooks
    notebook_files = [
        "Analysis/cache_aware_string_sorting.ipynb",
        "Analysis/cache_oblivious_string_sorting.ipynb"
    ]

    for filename in notebook_files:
        try:
            with open(filename, "r") as f:
                nb = json.load(f)
        except Exception:
            continue
        
        # Keep only markdown cells at the top (usually introductions)
        new_cells = []
        for cell in nb.get("cells", []):
            if cell["cell_type"] == "markdown":
                new_cells.append(cell)

        # Inject a more comprehensive code block
        code_source = [
            "import pandas as pd\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "from IPython.display import Image, display\n",
            "\n",
            "# Display pre-generated figures from Analysis/figures/\n",
            "figs = [\n",
            "    'figures/time_vs_n_random.png',\n",
            "    'figures/time_vs_n_wiki.png',\n",
            "    'figures/l1_vs_n_random.png',\n",
            "    'figures/llc_vs_n_wiki.png',\n",
            "    'figures/bar_time_large.png'\n",
            "]\n",
            "for fig in figs:\n",
            "    display(Image(filename=fig))\n"
        ]
        
        code_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": code_source
        }
        
        new_cells.append(code_cell)
        nb["cells"] = new_cells
        
        with open(filename, "w") as f:
            json.dump(nb, f, indent=1)
        print(f"Updated notebook: {filename}")

if __name__ == "__main__":
    main()