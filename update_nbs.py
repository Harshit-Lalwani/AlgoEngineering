import json
import sys

# Updated to use relative paths from the project root
files = [
    "Analysis/cache_aware_string_sorting.ipynb",
    "Analysis/cache_oblivious_string_sorting.ipynb"
]

for filename in files:
    with open(filename, "r") as f:
        nb = json.load(f)
    
    new_cells = []
    for cell in nb["cells"]:
        if cell["cell_type"] == "markdown":
            new_cells.append(cell)
            
    import_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import pandas as pd\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "import platform, subprocess, os, re\n",
            "import numpy as np\n",
            "\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "# load timing results and cache profiling results (try multiple relative paths)\n",
            "def _find_existing(paths):\n",
            "    for p in paths:\n",
            "        if os.path.exists(p):\n",
            "            return p\n",
            "    return None\n",
            "results_paths = [\"Analysis/results.csv\", \"results.csv\", \"../results.csv\"]\n",
            "cache_paths = [\"Analysis/cache_results.csv\", \"cache_results.csv\", \"../cache_results.csv\"]\n",
            "results_file = _find_existing(results_paths)\n",
            "cache_file = _find_existing(cache_paths)\n",
            "if results_file is None:\n",
            "    raise FileNotFoundError(\"results.csv not found in any of: %s\" % results_paths)\n",
            "if cache_file is None:\n",
            "    raise FileNotFoundError(\"cache_results.csv not found in any of: %s\" % cache_paths)\n",
            "results_df = pd.read_csv(results_file)\n",
            "cache_df = pd.read_csv(cache_file)\n",
            "# compute average string length S from total_length / count in cache_df\n",
            "cache_df['avg_string_length'] = cache_df['total_length'] / cache_df['count']\n",
            "\n",
            "# detect M and B (LLC size and cache line size) if not present in cache_df\n",
            "def parse_size_str(s):\n",
            "    s = s.strip()\n",
            "    if s.endswith(('K','k')):\n",
            "        return int(float(s[:-1]) * 1024)\n",
            "    if s.endswith(('M','m')):\n",
            "        return int(float(s[:-1]) * 1024 * 1024)\n",
            "    try:\n",
            "        return int(s)\n",
            "    except:\n",
            "        return None\n",
            "\n",
            "M = cache_df['M'].dropna().iloc[0] if 'M' in cache_df.columns and cache_df['M'].notna().any() else None\n",
            "B = cache_df['B'].dropna().iloc[0] if 'B' in cache_df.columns and cache_df['B'].notna().any() else None\n",
            "if M is None or B is None:\n",
            "    if platform.system() == 'Darwin':\n",
            "        try:\n",
            "            M = int(subprocess.check_output(['sysctl','-n','hw.l3cachesize']).strip())\n",
            "        except Exception:\n",
            "            M = None\n",
            "        try:\n",
            "            B = int(subprocess.check_output(['sysctl','-n','hw.cachelinesize']).strip())\n",
            "        except Exception:\n",
            "            B = None\n",
            "    else:\n",
            "        try:\n",
            "            idx3 = '/sys/devices/system/cpu/cpu0/cache/index3/size'\n",
            "            if os.path.exists(idx3):\n",
            "                with open(idx3) as f:\n",
            "                    M = parse_size_str(f.read().strip())\n",
            "        except Exception:\n",
            "            M = None\n",
            "        try:\n",
            "            path = '/sys/devices/system/cpu/cpu0/cache/index3/coherency_line_size'\n",
            "            if not os.path.exists(path):\n",
            "                path = '/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size'\n",
            "            if os.path.exists(path):\n",
            "                with open(path) as f:\n",
            "                    B = int(f.read().strip())\n",
            "        except Exception:\n",
            "            B = None\n",
            "\n",
            "print('Detected M=', M, 'B=', B)\n",
            "\n",
            "# extract burstsort threshold from header (fallback to 8192)\n",
            "burst_threshold = 8192\n",
            "try:\n",
            "    with open('cpp/src/algorithms/burstsort.hpp') as f:\n",
            "        txt = f.read()\n",
            "        m = re.search(r'default\\s*=\\s*(\\d+)', txt) or re.search(r'threshold\\s*=\\s*(\\d+)', txt)\n",
            "        if m:\n",
            "            burst_threshold = int(m.group(1))\n",
            "except Exception:\n",
            "    pass\n",
            "\n",
            "# compute theoretical Q approximations (bytes transferred / B) on timing data\n",
            "# also compute Q_theory on cache_df for miss comparisons\n",
            "passes = 1\n",
            "cache_df['N'] = cache_df['count']\n",
            "cache_df['S'] = cache_df['avg_string_length']\n",
            "cache_df['total_chars'] = cache_df['N'] * cache_df['S']\n",
            "cache_df.loc[cache_df['algorithm']=='msd_radix_sort', 'Q_theory'] = (cache_df['total_chars'] * passes) / (B if B else 1)\n",
            "cache_df.loc[cache_df['algorithm'].str.contains('burst', na=False), 'Q_theory'] = (cache_df['N'] * cache_df['S'].clip(upper=burst_threshold)) / (B if B else 1)\n",
            "mask_merge_cache = cache_df['algorithm']=='lazy_funnelsort'\n",
            "cache_df.loc[mask_merge_cache, 'Q_theory'] = (cache_df.loc[mask_merge_cache, 'total_chars'] / (B if B else 1)) * np.log2(cache_df.loc[mask_merge_cache, 'N'])\n",
            "mask_std_cache = cache_df['algorithm']=='std::sort'\n",
            "cache_df.loc[mask_std_cache, 'Q_theory'] = (cache_df.loc[mask_std_cache, 'total_chars'] / (B if B else 1)) * np.log2(cache_df.loc[mask_std_cache, 'N'])\n",
            "\n",
            "results_df['avg_string_length'] = results_df['total_length'] / results_df['count']\n",
            "results_df['N'] = results_df['count']\n",
            "results_df['S'] = results_df['avg_string_length']\n",
            "results_df['total_chars'] = results_df['N'] * results_df['S']\n",
            "results_df.loc[results_df['algorithm']=='msd_radix_sort', 'Q_theory'] = (results_df['total_chars'] * passes) / (B if B else 1)\n",
            "results_df.loc[results_df['algorithm'].str.contains('burst', na=False), 'Q_theory'] = (results_df['N'] * results_df['S'].clip(upper=burst_threshold)) / (B if B else 1)\n",
            "mask_merge = results_df['algorithm']=='lazy_funnelsort'\n",
            "results_df.loc[mask_merge, 'Q_theory'] = (results_df.loc[mask_merge, 'total_chars'] / (B if B else 1)) * np.log2(results_df.loc[mask_merge, 'N'])\n",
            "mask_std = results_df['algorithm']=='std::sort'\n",
            "results_df.loc[mask_std, 'Q_theory'] = (results_df.loc[mask_std, 'total_chars'] / (B if B else 1)) * np.log2(results_df.loc[mask_std, 'N'])\n",
            "\n",
            "# use timing data for plots to avoid NaNs from mismatched cache counts\n",
            "df = results_df\n",
            "df.head()\n"
        ]
    }
    
    plot_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(10, 6))\n",
            "sns.lineplot(data=df[df[\"dataset\"] == \"random\"], x=\"count\", y=\"elapsed_seconds\", hue=\"algorithm\", marker=\"o\")\n",
            "plt.title(\"Sorting Performance (Synthetic Random)\")\n",
            "plt.ylabel(\"Time (Seconds)\")\n",
            "plt.xlabel(\"Number of Strings\")\n",
            "plt.show()"
        ]
    }

    plot_cell2 = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(10, 6))\n",
            "sns.lineplot(data=df[df[\"dataset\"] == \"prefix_heavy\"], x=\"count\", y=\"elapsed_seconds\", hue=\"algorithm\", marker=\"o\")\n",
            "plt.title(\"Sorting Performance (Synthetic Prefix Heavy)\")\n",
            "plt.ylabel(\"Time (Seconds)\")\n",
            "plt.xlabel(\"Number of Strings\")\n",
            "plt.show()"
        ]
    }

    plot_cell3 = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(10, 6))\n",
            "sns.lineplot(data=df[df[\"dataset\"] == \"wiki_random\"], x=\"count\", y=\"elapsed_seconds\", hue=\"algorithm\", marker=\"o\")\n",
            "plt.title(\"Sorting Performance (Wikipedia Random)\")\n",
            "plt.ylabel(\"Time (Seconds)\")\n",
            "plt.xlabel(\"Number of Strings\")\n",
            "plt.show()"
        ]
    }

    plot_cell4 = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(10, 6))\n",
            "sns.lineplot(data=df[df[\"dataset\"] == \"wiki_heavy\"], x=\"count\", y=\"elapsed_seconds\", hue=\"algorithm\", marker=\"o\")\n",
            "plt.title(\"Sorting Performance (Wikipedia Long Titles)\")\n",
            "plt.ylabel(\"Time (Seconds)\")\n",
            "plt.xlabel(\"Number of Strings\")\n",
            "plt.show()"
        ]
    }

    plot_cell5 = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(10, 6))\n",
            "miss_df = cache_df.dropna(subset=[\"Q_theory\", \"lld_misses\"])\n",
            "sns.scatterplot(data=miss_df, x=\"Q_theory\", y=\"lld_misses\", hue=\"algorithm\", style=\"dataset\", alpha=0.8)\n",
            "plt.xscale(\"log\")\n",
            "plt.yscale(\"log\")\n",
            "plt.title(\"Q_theory vs LLC Misses (Cache Profile)\")\n",
            "plt.xlabel(\"Q_theory (approx cache lines)\")\n",
            "plt.ylabel(\"LLC Misses\")\n",
            "plt.show()"
        ]
    }

    plot_cell6 = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(10, 6))\n",
            "miss_df = cache_df.dropna(subset=[\"lld_misses\", \"total_length\", \"count\"])\n",
            "miss_df = miss_df.assign(misses_per_char=miss_df[\"lld_misses\"] / miss_df[\"total_length\"], misses_per_string=miss_df[\"lld_misses\"] / miss_df[\"count\"])\n",
            "sns.scatterplot(data=miss_df, x=\"count\", y=\"misses_per_char\", hue=\"algorithm\", style=\"dataset\", alpha=0.8)\n",
            "plt.xscale(\"log\")\n",
            "plt.yscale(\"log\")\n",
            "plt.title(\"LLC Misses per Character (Cache Profile)\")\n",
            "plt.xlabel(\"Number of Strings\")\n",
            "plt.ylabel(\"Misses per Character\")\n",
            "plt.show()"
        ]
    }
    
    new_cells.insert(1, import_cell)
    new_cells.append(plot_cell)
    new_cells.append(plot_cell2)
    new_cells.append(plot_cell3)
    new_cells.append(plot_cell4)
    new_cells.append(plot_cell5)
    new_cells.append(plot_cell6)
    
    nb["cells"] = new_cells
    
    with open(filename, "w") as f:
        json.dump(nb, f, indent=1)
    print("Updated", filename)