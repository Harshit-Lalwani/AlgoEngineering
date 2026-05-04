import json
import sys

files = [
    "/root/IAE/AlgoEngineering/Analysis/cache_aware_string_sorting.ipynb",
    "/root/IAE/AlgoEngineering/Analysis/cache_oblivious_string_sorting.ipynb"
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
            "plt.title(\"Sorting Performance (Random Dataset)\")\n",
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
            "plt.title(\"Sorting Performance (Prefix Heavy Dataset)\")\n",
            "plt.ylabel(\"Time (Seconds)\")\n",
            "plt.xlabel(\"Number of Strings\")\n",
            "plt.show()"
        ]
    }
    
    new_cells.insert(1, import_cell)
    new_cells.append(plot_cell)
    new_cells.append(plot_cell2)
    
    nb["cells"] = new_cells
    
    with open(filename, "w") as f:
        json.dump(nb, f, indent=1)
    print("Updated", filename)
