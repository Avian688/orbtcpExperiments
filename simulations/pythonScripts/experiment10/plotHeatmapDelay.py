import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

# ─── Matplotlib Styling ───────────────────────────────────────────────────────
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif']  = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams['font.weight'] = 'normal'
plt.rcParams['font.size']   = 40
plt.rcParams['text.usetex'] = True

# ─── Directory Roots ──────────────────────────────────────────────────────────
BASE_DIR  = os.path.join("..", "..", "..", "paperExperiments")
PING_ROOT = os.path.join(BASE_DIR, "experiment10", "csvs", "ping")
SRTT_ROOT = os.path.join(BASE_DIR, "experiment10", "csvs")

# ─── Experiment Parameters ────────────────────────────────────────────────────
pairs       = ['Pair1', 'Pair3']
pair_labels = {'Pair1': 'Pair1', 'Pair3': 'Pair2'}
protocols   = ['cubic', 'bbr', 'bbr3', 'orbtcp']
RUNS        = [1, 2, 3, 4, 5]
PROTOCOLS_FRIENDLY_NAME_LEO = {
    'cubic':  'Cubic',
    'bbr':    'BBRv1',
    'orbtcp': 'LeoTCP',
    'bbr3':   'BBRv3'
}

# Define which ping modules correspond to each pair (gs_index, app_index)
ping_modules = {
    'Pair1': [(2, 0), (2, 1)],  # groundStation[2].app[0] & [2].app[1]
    'Pair3': [(0, 0), (29, 0)]   # groundStation[0].app[0] & [29].app[0]
}

# Row labels for heatmap
row_labels = [pair_labels[p] for p in pairs]

# ─── Helper: per-second Average ───────────────────────────────────────────────
def avg_per_second(filepath, col):
    df = pd.read_csv(filepath)
    df['time_s'] = df['time'].astype(float).astype(int)
    vals = df.groupby('time_s')[col].mean()
    avg = vals.mean()
    print(f"[DEBUG] avg_per_second: {filepath} -> avg {avg:.4f} s")
    return avg

# ─── Compute Normalized Delay ─────────────────────────────────────────────────
def compute_mean_std_normalised(pair, proto):
    print(f"[DEBUG] Computing normalized delay for pair='{pair}', protocol='{proto}'")
    # Aggregate base RTT from multiple ping modules
    base_rtts = []
    for gs_idx, app_idx in ping_modules[pair]:
        ping_file = os.path.join(
            PING_ROOT,
            'isl',
            f"leoconstellation.groundStation[{gs_idx}].app[{app_idx}]",
            'rtt.csv'
        )
        print(f"[DEBUG] Checking ping file: {ping_file}")
        if os.path.exists(ping_file):
            rtt_val = avg_per_second(ping_file, 'rtt')
            base_rtts.append(rtt_val)
    if not base_rtts:
        print(f"[DEBUG] No base RTT values found for {pair}")
        return 0.0, 0.0
    base_rtt = np.mean(base_rtts)
    print(f"[DEBUG] base_rtts for {pair}: {base_rtts}, mean={base_rtt:.4f} s")

    # Collect SRTT from client flows
    flow_runs = {0: [], 1: []}
    for run in RUNS:
        for flow in [0, 1]:
            rtt_file = os.path.join(
                SRTT_ROOT,
                proto.title(),
                pair,
                f"run{run}",
                f"leoconstellation.client[{flow}].tcp.conn",
                'rtt.csv'
            )
            print(f"[DEBUG] Checking SRTT file: {rtt_file}")
            if os.path.exists(rtt_file):
                run_val = avg_per_second(rtt_file, 'rtt')
                flow_runs[flow].append(run_val)
                print(f"[DEBUG] SRTT for {pair}, protocol={proto}, run{run}, flow{flow}: {run_val:.4f} s")
    if not flow_runs[0] or not flow_runs[1]:
        print(f"[DEBUG] Missing SRTT runs for {pair}, protocol={proto}")
        return 0.0, 0.0

    # Compute raw and normalized statistics
    mean0, mean1 = np.mean(flow_runs[0]), np.mean(flow_runs[1])
    std0, std1   = np.std(flow_runs[0]), np.std(flow_runs[1])
    mu_raw    = np.mean([mean0, mean1])
    sigma_raw = np.sqrt((std0**2 + std1**2) / 2)
    mu_norm    = mu_raw / base_rtt
    sigma_norm = sigma_raw / base_rtt
    print(f"[DEBUG] Normalized values for {pair}, protocol={proto}: mu_norm={mu_norm:.4f}, sigma_norm={sigma_norm:.4f}")
    return mu_norm, sigma_norm

# ─── Build DataFrames ─────────────────────────────────────────────────────────
df_mean = pd.DataFrame(index=row_labels, columns=protocols, dtype=float)
df_std  = pd.DataFrame(index=row_labels, columns=protocols, dtype=float)
for p, label in zip(pairs, row_labels):
    for proto in protocols:
        mu, sigma = compute_mean_std_normalised(p, proto)
        df_mean.at[label, proto] = mu
        df_std.at[label, proto]   = sigma

# ─── Heatmap Plotting ─────────────────────────────────────────────────────────
cmap = LinearSegmentedColormap.from_list('g_y_r', ['green', 'yellow', 'red'], N=256)
fig, ax = plt.subplots(figsize=(10, 7))
df = df_mean
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
    fontsize=24
)

# Hide Y-axis ticks
ax.set_yticks(np.arange(len(row_labels)))
ax.tick_params(axis='y', which='both', labelleft=False)

# Annotate each cell
for i in range(df.shape[0]):
    for j in range(df.shape[1]):
        mu = df.iat[i, j]
        sigma = df_std.iat[i, j]
        ax.text(j, i, f"{mu:.2f}±{sigma:.2f}", ha='center', va='center', fontsize=20)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.ax.tick_params(labelsize=24)

plt.subplots_adjust(left=0.1, right=0.84, top=0.98, bottom=0.15)
plt.savefig('heatmap_normalized_delay_pairs_exp10.pdf', dpi=1080, bbox_inches='tight')
plt.close(fig)

# ─── Separate Legend ─────────────────────────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(10, 7))
ax2.set_yticks(np.arange(len(row_labels)))
ax2.set_yticklabels(row_labels, fontsize=28)
ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
ax2.tick_params(axis='y', length=0)
for spine in ax2.spines.values():
    spine.set_visible(False)
plt.savefig('path_legend_pairs_exp10.pdf', dpi=1080, pad_inches=0)