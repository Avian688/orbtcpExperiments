import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

# Plot styling (same as previous script)
import scienceplots
plt.style.use('science')

plt.rcParams['font.size'] = 40
plt.rcParams['text.usetex'] = True

# Directory roots
BASE_DIR  = os.path.join("..", "..", "..", "paperExperiments")
PING_ROOT = os.path.join(BASE_DIR, "experiment8", "csvs", "ping")
SRTT_ROOT = os.path.join(BASE_DIR, "experiment9", "csvs")

# Experiment parameters
protocols = ['cubic', 'bbr', 'bbr3', 'orbtcp']
RUNS      = [1, 2, 3, 4, 5]
QMULTS    = [1]
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
PROTOCOLS_FRIENDLY_NAME_LEO = {
    'cubic':  'Cubic',
    'bbr':    'BBRv1',
    'orbtcp': 'LeoTCP',
    'bbr3':   'BBRv3'
}

# Paths and labels
t_paths = {
    "SeattleNewYork_isl":      {"label": "SEA to NY (ISL)", "ping_app_index": 0},
    "SeattleNewYork_bentpipe": {"label": "SEA to NY (BP)",  "ping_app_index": 0},
    "SanDiegoNewYork_isl":     {"label": "SD to NY (ISL)", "ping_app_index": 1},
    "SanDiegoNewYork_bentpipe":{"label": "SD to NY (BP)",  "ping_app_index": 1},
    "NewYorkLondon_isl":       {"label": "NY to LDN (ISL)","ping_app_index": 0},
    "SanDiegoShanghai_isl":    {"label": "SD to SHA (ISL)","ping_app_index": 2}
}
location_to_gs_index = {
    "NewYork":  2,
    "London":   3,
    "SanDiego": 0,
    "Shanghai": 4,
    "Seattle":  1
}
path_keys  = list(t_paths.keys())
row_labels = [t_paths[k]['label'] for k in path_keys]

# Helper: per-100ms average of a column in CSV
def avg_per_100ms(filepath, col):
    df = pd.read_csv(filepath)
    df['time_ds'] = (df['time'].astype(float) * 10).round().astype(int)
    per_ds = df.groupby('time_ds')[col].mean()
    return per_ds.mean()

# Compute normalized mean±std delay
def compute_mean_std_normalised(key, proto, m):
    before, after = key.split('_', 1)
    gs_idx  = next(idx for loc, idx in location_to_gs_index.items() if before.startswith(loc))
    app_idx = t_paths[key]['ping_app_index']

    # Base RTT avg per 100ms
    ping_file = os.path.join(
        PING_ROOT,
        after,
        f"leoconstellation.groundStation[{gs_idx}].app[{app_idx}]",
        'rtt.csv'
    )
    if not os.path.exists(ping_file):
        return 0.0, 0.0
    base_rtt = avg_per_100ms(ping_file, 'rtt')

    # Client-run means (two flows) per 100ms
    flow0_runs, flow1_runs = [], []
    for run in RUNS:
        for flow, lst in [(0, flow0_runs), (1, flow1_runs)]:
            rtt_file = os.path.join(
                SRTT_ROOT,
                proto.title(),
                before,
                after,
                QMULTDICT[m],
                f"run{run}",
                f"leoconstellation.client[{flow}].tcp.conn",
                'rtt.csv'
            )
            if not os.path.exists(rtt_file):
                continue
            ds_mean = avg_per_100ms(rtt_file, 'rtt')
            lst.append(ds_mean)

    if not flow0_runs or not flow1_runs:
        return 0.0, 0.0

    mean0, mean1 = np.mean(flow0_runs), np.mean(flow1_runs)
    std0,  std1  = np.std(flow0_runs),  np.std(flow1_runs)
    mu_raw    = np.mean([mean0, mean1])
    sigma_raw = np.sqrt((std0**2 + std1**2) / 2)

    mu_norm    = mu_raw / base_rtt    if base_rtt else 0.0
    sigma_norm = sigma_raw / base_rtt if base_rtt else 0.0
    return mu_norm, sigma_norm

# Build heatmap data
df_mean, df_std = {}, {}
for m in QMULTS:
    mean_df = pd.DataFrame(index=row_labels, columns=protocols, dtype=float)
    std_df  = pd.DataFrame(index=row_labels, columns=protocols, dtype=float)
    for key, label in zip(path_keys, row_labels):
        for proto in protocols:
            mu, sigma = compute_mean_std_normalised(key, proto, m)
            mean_df.at[label, proto] = mu
            std_df.at[label, proto]   = sigma
    df_mean[m] = mean_df
    df_std[m]  = std_df

# ========== Heatmap (no left legend) ==========
cmap = LinearSegmentedColormap.from_list('g_y_r', ['green', 'yellow', 'red'], N=256)

fig, ax = plt.subplots(figsize=(10, 7))
df = df_mean[QMULTS[0]]

# Normalize over actual data range
dyn_min, dyn_max = df.values.min(), df.values.max()
norm = Normalize(vmin=dyn_min, vmax=dyn_max)

im = ax.imshow(
    df.values,
    origin='upper',
    aspect='auto',
    cmap=cmap,
    norm=norm,
    interpolation='nearest'
)

# Bottom protocol labels
ax.set_xticks(np.arange(len(protocols)))
ax.set_xticklabels(
    [PROTOCOLS_FRIENDLY_NAME_LEO[p] for p in protocols],
    rotation=0,
    ha='center',
    fontsize=27
)

# Hide Y-axis labels
ax.set_yticks(np.arange(len(row_labels)))
ax.tick_params(axis='y', which='both', labelleft=False)

# Annotate each cell
for i in range(df.shape[0]):
    for j in range(df.shape[1]):
        mu = df.iat[i, j]
        sigma = df_std[QMULTS[0]].iat[i, j]
        ax.text(
            j,
            i,
            f"{mu:.2f}±{sigma:.2f}",
            ha='center',
            va='center',
            fontsize=23
        )

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
#cbar.set_label(
#    "Mean Norm. Delay",
#    rotation=90,
#    fontsize=34,
#    labelpad=20
#)
cbar.ax.tick_params(labelsize=27)

plt.subplots_adjust(left=0.1, right=0.84, top=0.98, bottom=0.15)
plt.savefig('heatmap_no_legend.pdf', dpi=1080, bbox_inches='tight')

# ========== Separate Legend ==========
fig2, ax2 = plt.subplots(figsize=(10, 7))

# Y-ticks and labels (larger font)
ax2.set_yticks(np.arange(len(row_labels)))
ax2.set_yticklabels(
    row_labels,
    fontsize=28
)

# Hide x-axis ticks/labels and y-tick lines
ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
ax2.tick_params(axis='y', length=0)

# Hide all spines
for spine in ax2.spines.values():
    spine.set_visible(False)

# Tight layout & save with no extra padding
#plt.tight_layout(pad=0)
plt.savefig(
    'path_legend.pdf',
    dpi=1080,
    pad_inches=0
)