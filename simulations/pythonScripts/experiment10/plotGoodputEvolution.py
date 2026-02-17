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

# ─── Experiment Setup ─────────────────────────────────────────────────────────
pairs2      = ['Pair1', 'Pair3']
pair_labels = {'Pair1': 'Pair1', 'Pair3': 'Pair2'}

protocols   = ['cubic', 'bbr', 'bbr3', 'orbtcp']
RUNS        = [1, 2, 3, 4, 5]

FRIENDLY    = {'cubic':'Cubic',
               'bbr':'BBRv1',
               'bbr3':'BBRv3',
               'orbtcp':'LeoTCP'}

# ─── Helper to compute per‐time‐point stats via global interpolation ────────
def timeseries_stats(proto, pair):
    """Return DataFrame with columns time, mean0, std0, mean1, std1 (bps)."""
    base = os.path.join("../../../paperExperiments/experiment10/csvs",
                        proto.title(), pair)
    runs_data = {0: [], 1: []}

    # collect raw time & goodput arrays per run/server
    for run in RUNS:
        for srv in (0, 1):
            path = os.path.join(base,
                                f"run{run}",
                                f"leoconstellation.server[{srv}].app[0]",
                                "goodput.csv")
            if os.path.exists(path):
                df = pd.read_csv(path)
                if {'time','goodput'}.issubset(df.columns):
                    runs_data[srv].append((df['time'].values,
                                           df['goodput'].values))

    # sanity: need data for both servers
    if not runs_data[0] or not runs_data[1]:
        return pd.DataFrame()

    # determine global common time window & step
    starts = [t_arr[0]   for srv in runs_data for t_arr, _ in runs_data[srv]]
    ends   = [t_arr[-1]  for srv in runs_data for t_arr, _ in runs_data[srv]]
    dts    = [np.median(np.diff(t_arr)) for srv in runs_data for t_arr, _ in runs_data[srv]]
    t0, t1 = max(starts), min(ends)
    dt      = float(min(dts))
    time_grid = np.arange(t0, t1 + dt/2, dt)

    # interpolate per server onto the common grid
    stats = {}
    for srv in (0, 1):
        arrs = []
        for t_arr, g_arr in runs_data[srv]:
            arrs.append(np.interp(time_grid, t_arr, g_arr))
        stacked = np.vstack(arrs)  # shape: (n_runs_srv, len(time_grid))
        stats[srv] = (stacked.mean(axis=0), stacked.std(axis=0))

    mu0, s0 = stats[0]
    mu1, s1 = stats[1]

    return pd.DataFrame({
        'time':  time_grid,
        'mean0': mu0,
        'std0':  s0,
        'mean1': mu1,
        'std1':  s1,
    })

# ─── Plot all combinations ────────────────────────────────────────────────────
for proto in protocols:
    for pair in pairs2:
        df_ts = timeseries_stats(proto, pair)
        if df_ts.empty:
            print(f"No data for {proto} / {pair}, skipping.")
            continue

        # convert from bps to Mbps
        df_ts[['mean0','std0','mean1','std1']] /= 1e6

        plt.figure(figsize=(12, 6))
        plt.plot(df_ts['time'], df_ts['mean0'],
                 label='Flow 0', color='tab:blue', linewidth=2)
        plt.fill_between(df_ts['time'],
                         df_ts['mean0'] - df_ts['std0'],
                         df_ts['mean0'] + df_ts['std0'],
                         alpha=0.3, color='tab:blue')

        plt.plot(df_ts['time'], df_ts['mean1'],
                 label='Flow 1', color='tab:orange', linewidth=2)
        plt.fill_between(df_ts['time'],
                         df_ts['mean1'] - df_ts['std1'],
                         df_ts['mean1'] + df_ts['std1'],
                         alpha=0.3, color='tab:orange')

        plt.xlabel('Time (s)', fontsize=24)
        plt.ylabel('Goodput (Mbps)', fontsize=24)
        plt.title(f'{FRIENDLY[proto]} — {pair_labels[pair]}', fontsize=28)
        plt.legend(fontsize=20)
        plt.grid(True, linestyle='--', linewidth=0.5)
        plt.tight_layout()

        outfname = f'goodput_ts_{proto}_{pair}.pdf'
        plt.savefig(outfname, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved plot to {outfname}")