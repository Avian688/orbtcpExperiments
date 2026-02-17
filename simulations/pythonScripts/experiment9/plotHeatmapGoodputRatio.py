import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

# Set up LaTeX fonts and style
import scienceplots
plt.style.use('science')

plt.rcParams['font.size'] = 40
plt.rcParams['text.usetex'] = True

# Protocols and runs
protocols = ['cubic', 'bbr', 'bbr3', 'orbtcp']
RUNS = [1, 2, 3, 4, 5]
QMULTS = [1]  # only medium buffer
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
PROTOCOLS_FRIENDLY_NAME_LEO = {
    'cubic': 'Cubic',
    'bbr': 'BBRv1',
    'orbtcp': 'LeoTCP',
    'bbr3': 'BBRv3'
}

# Path information
paths_info = {
    "SeattleNewYork_isl":      {"queue": 388, "label": "SEA to NY (ISL)"},
    "SeattleNewYork_bentpipe": {"queue": 326, "label": "SEA to NY (BP)"},
    "SanDiegoNewYork_isl":     {"queue": 522, "label": "SD to NY (ISL)"},
    "SanDiegoNewYork_bentpipe":{"queue": 408, "label": "SD to NY (BP)"},
    "NewYorkLondon_isl":       {"queue": 696, "label": "NY to LDN (ISL)"},
    "SanDiegoShanghai_isl":    {"queue": 740, "label": "SD to SHA (ISL)"}
}

path_keys  = list(paths_info.keys())
row_labels = [paths_info[k]["label"] for k in path_keys]

def compute_mean_std_normalised_ratio(path_key, proto, m):
    before, after = path_key.split("_", 1)
    base_path = os.path.join(
        "../../../paperExperiments/experiment9/csvs",
        proto.title(), before, after,
        QMULTDICT[m]
    )

    ratios = []
    for run in RUNS:
        run_path = os.path.join(base_path, f"run{run}")
        gp0 = os.path.join(run_path, "leoconstellation.server[0].app[0]", "goodput.csv")
        gp1 = os.path.join(run_path, "leoconstellation.server[1].app[0]", "goodput.csv")
        if not os.path.exists(gp0) or not os.path.exists(gp1):
            print(f"Missing goodput file: {gp0 if not os.path.exists(gp0) else gp1}")
            continue

        df0, df1 = pd.read_csv(gp0), pd.read_csv(gp1)
        if "goodput" not in df0 or "goodput" not in df1:
            continue

        g0, g1 = df0["goodput"].mean(), df1["goodput"].mean()
        if g0 > 0 and g1 > 0:
            ratios.append(min(g0, g1) / max(g0, g1))

    if ratios:
        return float(np.mean(ratios)), float(np.std(ratios))
    else:
        return 0.0, 0.0

# Build dataframes for mean and std
df_mean, df_std = {}, {}
for m in QMULTS:
    mdf = pd.DataFrame(index=row_labels, columns=protocols, data=0.0)
    sdf = pd.DataFrame(index=row_labels, columns=protocols, data=0.0)
    for key, label in zip(path_keys, row_labels):
        for proto in protocols:
            mu, sigma = compute_mean_std_normalised_ratio(key, proto, m)
            mdf.at[label, proto] = mu
            sdf.at[label, proto] = sigma
    df_mean[m], df_std[m] = mdf, sdf

# Define colormap: red → yellow → green
cmap = LinearSegmentedColormap.from_list("r_y_g", ["red", "yellow", "green"], N=256)
# Normalize colorbar from 0.5 to 1.0
norm = Normalize(vmin=0.5, vmax=1.0)

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 7))

mdf, sdf = df_mean[1], df_std[1]
im = ax.imshow(
    mdf.values, origin="upper", aspect="auto",
    cmap=cmap, norm=norm, interpolation="nearest"
)

# X-axis (protocols)
ax.set_xticks(np.arange(len(protocols)))
ax.set_xticklabels(
    [PROTOCOLS_FRIENDLY_NAME_LEO[p] for p in protocols],
    rotation=0, ha="center", fontsize=27
)

# Y-axis ticks (hide labels)
ax.set_yticks(np.arange(len(row_labels)))
ax.tick_params(axis='y', which='both', labelleft=False)

# Annotate each cell
for i in range(mdf.shape[0]):
    for j in range(mdf.shape[1]):
        mu, sigma = mdf.iat[i, j], sdf.iat[i, j]
        ax.text(
            j, i, f"{mu:.2f}±{sigma:.2f}",
            ha="center", va="center",
            color="black", fontsize=25
        )

# Colorbar from 0.5 to 1.0 with custom ticks
cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.83])
cb = fig.colorbar(im, cax=cbar_ax)
#cb.set_label("Mean Goodput Ratio", labelpad=20, rotation=90, fontsize=34)
cb.set_ticks([0.5, 0.75, 1.0])
cb.ax.tick_params(labelsize=27)
cb.ax.yaxis.set_label_position('right')
cb.ax.yaxis.tick_right()

plt.subplots_adjust(left=0.10, right=0.84, top=0.98, bottom=0.15)
plt.savefig("heatmap_goodput_fairness.pdf", dpi=1080, bbox_inches="tight")