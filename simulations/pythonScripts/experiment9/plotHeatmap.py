import os, sys, glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib import font_manager

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams['font.weight'] = 'bold'
plt.rcParams['font.size'] = 40
plt.rcParams['text.usetex'] = True


protocols = ['cubic', 'bbr', 'orbtcp', 'bbr3']

bent_pipe_link_bandwidth = 100
num_flows               = 1

RUNS = [1, 2, 3, 4, 5]
QMULTS = [0.2, 1 ,4]
QMULTDICT = {0.2 : "smallbuffer", 1 : "mediumbuffer", 4 : "largebuffer" }
PROTOCOLS_FRIENDLY_NAME_LEO = {
        'cubic':   'Cubic',
        'bbr':    'BBRv1',
        'orbtcp':    'OrbTCP',
        'bbr3':    'BBRv3'    
    }

# Combine “basename (no .log)” → {queue, label}
paths_info = {
    # "SanDiegoSeattle_isl":     { "queue": 582, "label": "San Diego to Seattle (ISL)" },
    # "SanDiegoSeattle_bentpipe":      { "queue": 219, "label": "San Diego to Seattle (BP)" },
    "SeattleNewYork_isl":     { "queue": 388, "label": "Seattle to New York (ISL)" },
    "SeattleNewYork_bentpipe":      { "queue": 326, "label": "Seattle to New York (BP)" },
    "SanDiegoNewYork_isl":      { "queue": 522, "label": "San Diego to New York (ISL)" },
    "SanDiegoNewYork_bentpipe":       { "queue": 408, "label": "San Diego to New York (BP)" },
    "NewYorkLondon_isl":     { "queue": 696, "label": "New York to London (ISL)" },
    "SanDiegoShanghai_isl":{ "queue": 740, "label": "San Diego to Shanghai (ISL)" }
}


# Mapping from second location to ground station index
location_to_gs_index = {
    "NewYork": 2,
    "London": 3,
    "Shanghai": 4,
    "Seattle": 1
}

path_keys  = list(paths_info.keys())
row_labels = [paths_info[k]["label"] for k in path_keys]

def compute_mean_std(path_key, proto, m):
    base_q    = paths_info[path_key]["queue"]
    switch_q  = int(base_q * m)
    run_values = []
    for run in RUNS:
        # Split the path_key into two parts
        path_key_before, path_key_after = path_key.split("_", 1)

        # Split the path_key into before and after underscore
        path_key_before, path_key_after = path_key.split("_", 1)

        # Extract second location from path_key_before
        # Assumes format like "SanDiegoSeattle"
        # Split using known prefixes or use regex or fixed length to extract second city
        # Here we assume camel case split (i.e., from a known position or pattern)
        # If it's always two concatenated city names, you could do:
        for loc in location_to_gs_index:
            if path_key_before.endswith(loc):
                second_location = loc
                break
        else:
            raise ValueError(f"Unknown second location in path_key: {path_key_before}")

        gs_index = location_to_gs_index[second_location]

        # Build the full path to the CSV
        PATH = f"../../../paperExperiments/experiment8/csvs/{proto.title()}/{path_key_before}/{path_key_after}/{QMULTDICT.get(m)}/run{run}/leoconstellation.groundStation[{gs_index}].app[0]/goodput.csv"
        csv_file = os.path.join(
            "..", "..", "..",
            "paperExperiments", "experiment8", "csvs", proto.title(),
            path_key_before,
            path_key_after,
            QMULTDICT.get(m),
            f"run{run}",
            f"leoconstellation.groundStation[{gs_index}].app[0]",
            "goodput.csv" 
        )

        if not os.path.exists(PATH):
            print("NOT FOUND: " + csv_file)
            continue
        #else:
            #print("FOUND: " + csv_file)


        file_means = []
        df = pd.read_csv(PATH)
        if "goodput" in df.columns:
            file_means.append(df["goodput"].mean()//1000000)

        if file_means:
            run_values.append(np.mean(file_means))

    if run_values:
        return float(np.mean(run_values)), float(np.std(run_values))
    else:
        return 0.0, 0.0

df_mean = {}
df_std  = {}

for m in QMULTS:
    dfm = pd.DataFrame(0.0, index=row_labels, columns=protocols)
    dfs = pd.DataFrame(0.0, index=row_labels, columns=protocols)
    for key, label in zip(path_keys, row_labels):
        for proto in protocols:
            mu, sigma = compute_mean_std(key, proto, m)
            dfm.at[label, proto] = mu
            dfs.at[label, proto] = sigma
    df_mean[m] = dfm
    df_std[m]  = dfs

# Create a continuous “red → yellow → green” colormap, fixed to [0, 100]
cmap = LinearSegmentedColormap.from_list("r_y_g", ["red", "yellow", "green"], N=256)
norm = Normalize(vmin=0, vmax=100)

fig, axes = plt.subplots(1, 3, figsize=(30, 8), sharey=False)

for idx, m in enumerate(QMULTS):
    ax  = axes[idx]
    dfm = df_mean[m]
    dfs = df_std[m]

    im = ax.imshow(
        dfm.values,
        origin="upper",
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        norm=norm
    )

    # X‐axis: use friendly names, but keep them horizontal
    ax.set_xticks(np.arange(len(protocols)))

    ax.set_xticklabels(
        [rf"\textbf{{{PROTOCOLS_FRIENDLY_NAME_LEO[p]}}}" for p in protocols],
        rotation=0,
        ha="center",
        fontsize=18
    )

    # Y‐axis: show path labels only on the leftmost subplot
    if idx == 0:
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_yticklabels([rf"\textbf{{{r}}}" for r in row_labels], fontsize=14)
    else:
        ax.set_yticks([])
        ax.set_yticklabels([])

    # Overlay “mean ± std” text inside each cell
    for i in range(dfm.shape[0]):
        for j in range(dfm.shape[1]):
            mu    = dfm.iat[i, j]
            sigma = dfs.iat[i, j]
            # Conditional text color: black if mean ∈ [40,70], otherwise white
            text_color = "black" # if 40 <= mu <= 70 else "white"
            ax.text(j, i,
                f"{mu:.1f}±{sigma:.1f}",
                ha="center", va="center",
                color=text_color,
                fontsize=18
            )
    # Subcaption below each heatmap


    letter = chr(97 + idx) 
    m_str  = f"{m}" 

    ax.text(
        0.5, -0.10,
        rf"\textbf{{({letter}) Buffer Size: }}{m_str}\(\times\)\textbf{{BDP}}",
        ha="center", va="top",
        transform=ax.transAxes,
        fontsize=34,
    )

# Place single colorbar on the far right; shift it leftward for more space
cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.83])
cb = fig.colorbar(im, cax=cbar_ax)
cb.set_label(rf"\textbf{{Mean Norm. Goodput}}", labelpad=+20, rotation=90, fontsize=30)
cb.ax.tick_params(labelsize=20)
cb.ax.yaxis.set_label_position('right')
cb.ax.yaxis.tick_right()

plt.subplots_adjust(left=0.10, right=0.88, top=0.98, bottom=0.15)

# Save to PDF
plt.savefig("heatmap_leo.pdf", dpi=1080)