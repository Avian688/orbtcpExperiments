import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams['font.weight'] = 'bold'
plt.rcParams['font.size'] = 40
plt.rcParams['text.usetex'] = False

protocols = ['cubic', 'bbr', 'orbtcp', 'bbr3']
RUNS = [1, 2, 3, 4, 5]
QMULTS = [1]
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
PROTOCOLS_FRIENDLY_NAME_LEO = {
    'cubic': 'Cubic',
    'bbr': 'BBRv1',
    'orbtcp': 'LeoTCP',
    'bbr3': 'BBRv3'
}

# Abbreviated path labels, with ISL/BP suffix
paths_info = {
    "SeattleNewYork_isl": {"queue": 388, "label": "SEA to NY (ISL)", "ping_app_index": 0},
    "SeattleNewYork_bentpipe": {"queue": 326, "label": "SEA to NY (BP)", "ping_app_index": 0},
    "SanDiegoNewYork_isl": {"queue": 522, "label": "SD to NY (ISL)", "ping_app_index": 1},
    "SanDiegoNewYork_bentpipe": {"queue": 408, "label": "SD to NY (BP)", "ping_app_index": 1},
    "NewYorkLondon_isl": {"queue": 696, "label": "NY to LDN (ISL)", "ping_app_index": 0},
    "SanDiegoShanghai_isl": {"queue": 740, "label": "SD to SHA (ISL)", "ping_app_index": 2}
}

location_to_gs_index = {
    "NewYork": 2,
    "London": 3,
    "SanDiego": 0,
    "Shanghai": 4,
    "Seattle": 1
}

path_keys = list(paths_info.keys())
row_labels = [paths_info[k]["label"] for k in path_keys]

def get_base_rtt_avg(path_key_after, gs_index, app_index):
    ping_path = os.path.join(
        "../../../paperExperiments/experiment8/csvs/ping",
        path_key_after,
        f"leoconstellation.groundStation[{gs_index}].app[{app_index}]",
        "rtt.csv"
    )
    if not os.path.exists(ping_path):
        print("BASE RTT FILE NOT FOUND: " + ping_path)
        return None

    df_ping = pd.read_csv(ping_path)
    if "time" not in df_ping.columns or "rtt" not in df_ping.columns:
        return None

    df_ping['time_sec'] = df_ping['time'].astype(float).round()
    grouped = df_ping.groupby("time_sec")["rtt"].mean()
    return grouped.mean()

def compute_mean_std_normalised(path_key, proto, m):
    path_key_before, path_key_after = path_key.split("_", 1)

    for loc in location_to_gs_index:
        if path_key_before.startswith(loc):
            first_location = loc
            break
    else:
        raise ValueError(f"Unknown first location in path_key: {path_key_before}")

    gs_index = location_to_gs_index[first_location]
    app_index = paths_info[path_key]["ping_app_index"]
    base_rtt = get_base_rtt_avg(path_key_after, gs_index, app_index)
    if base_rtt is None or base_rtt == 0:
        print(f"Skipping {path_key} due to missing base RTT")
        return 0.0, 0.0

    run_values = []
    for run in RUNS:
        srtt_path = os.path.join(
            "../../../paperExperiments/experiment8/csvs", proto.title(),
            path_key_before,
            path_key_after,
            QMULTDICT.get(m),
            f"run{run}",
            f"leoconstellation.groundStation[{gs_index}].tcp.conn",
            "srtt.csv"
        )

        if not os.path.exists(srtt_path):
            print("NOT FOUND: " + srtt_path)
            continue

        df = pd.read_csv(srtt_path)
        if "time" not in df.columns or "srtt" not in df.columns:
            continue

        df['time_sec'] = df['time'].astype(float).round()
        srtt_avg_per_sec = df.groupby("time_sec")["srtt"].mean()
        mean_srtt = srtt_avg_per_sec.mean()
        norm_srtt = mean_srtt / base_rtt
        run_values.append(norm_srtt)

    if run_values:
        return float(np.mean(run_values)), float(np.std(run_values))
    else:
        return 0.0, 0.0

# Build heatmap data
df_mean = {}
df_std = {}

for m in QMULTS:
    dfm = pd.DataFrame(0.0, index=row_labels, columns=protocols)
    dfs = pd.DataFrame(0.0, index=row_labels, columns=protocols)
    for key, label in zip(path_keys, row_labels):
        for proto in protocols:
            mu, sigma = compute_mean_std_normalised(key, proto, m)
            dfm.at[label, proto] = mu
            dfs.at[label, proto] = sigma
    df_mean[m] = dfm
    df_std[m] = dfs

# Flipped color map (green = good = low delay)
cmap = LinearSegmentedColormap.from_list("g_y_r", ["green", "yellow", "red"], N=256)
norm = Normalize(vmin=1.0, vmax=2.0)

fig, axes = plt.subplots(1, len(QMULTS), figsize=(10, 8), sharey=False)
if len(QMULTS) == 1:
    axes = [axes]

for idx, m in enumerate(QMULTS):
    ax = axes[idx]
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

    ax.set_xticks(np.arange(len(protocols)))
    ax.set_xticklabels(
        [rf"\textbf{{{PROTOCOLS_FRIENDLY_NAME_LEO[p]}}}" for p in protocols],
        rotation=0,
        ha="center",
        fontsize=18
    )

    if idx == 0:
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_yticklabels([rf"\textbf{{{r}}}" for r in row_labels], fontsize=20)
    else:
        ax.set_yticks([])
        ax.set_yticklabels([])

    for i in range(dfm.shape[0]):
        for j in range(dfm.shape[1]):
            mu = dfm.iat[i, j]
            sigma = dfs.iat[i, j]
            ax.text(j, i,
                    f"{mu:.2f}±{sigma:.2f}",
                    ha="center", va="center",
                    color="black",
                    fontsize=18
                    )

# Colorbar
cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.83])
cb = fig.colorbar(im, cax=cbar_ax)
#cb.set_label(r"\textbf{Mean Norm. Delay}", labelpad=+20, rotation=90, fontsize=30)
cb.set_ticks([1.0, 1.5, 2.0])
cb.ax.tick_params(labelsize=20)
cb.ax.yaxis.set_label_position('right')
cb.ax.yaxis.tick_right()

# Layout fix: more room for colorbar
plt.subplots_adjust(left=0.10, right=0.84, top=0.98, bottom=0.15)

# Save
plt.savefig("heatmap_leo_delay.pdf", dpi=1080, bbox_inches="tight")