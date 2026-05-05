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
            "\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "df = pd.read_csv(\"results.csv\")\n",
            "df.head()"
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
    
    new_cells.insert(1, import_cell)
    new_cells.append(plot_cell)
    new_cells.append(plot_cell2)
    new_cells.append(plot_cell3)
    new_cells.append(plot_cell4)
    
    nb["cells"] = new_cells
    
    with open(filename, "w") as f:
        json.dump(nb, f, indent=1)
    print("Updated", filename)