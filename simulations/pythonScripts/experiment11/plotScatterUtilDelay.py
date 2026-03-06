#!/usr/bin/env python3
import os, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
plt.style.use('science')
import matplotlib as mpl
mpl.rcParams['text.usetex'] = True
pd.set_option('display.max_rows', None)
plt.rcParams['axes.labelsize'] = "large"
plt.rcParams['xtick.labelsize'] = "large"
plt.rcParams['ytick.labelsize'] = "large"

from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

ROOT_PATH = "../../.."
EXPERIMENT = "experiment11"

# Experiment 11 settings
BANDWIDTH = 100                  # Mbps
BASE_RTT_MS = 50                 # ms
FLOW_BATCHES = [5, 10, 20]
PROTOCOLS = ['cubic','bbr','bbr3','satcp','leocc','orbtcp']
RUNS = [1,2,3,4,5]

# Evaluate after all flows have joined (latest join ~= 100s), and before end
EVAL_START = 105
EVAL_END   = 155

COLORS_LEO = {
    'cubic':'#0C5DA5',
    'bbr':'#00B945',
    'orbtcp':'#FF9500',
    'bbr3':'#eb0909',
    'satcp':'#8c5cff',
    'leocc':'#00b7c7'
}

MARKERS_BATCH = {
    5: 'o',
    10: '^',
    20: 's'
}


def confidence_ellipse(x, y, ax, n_std=1.0, facecolor='none', **kwargs):
    if x.size != y.size:
        raise ValueError("x and y must be the same size")
    if x.size < 2:
        return None
    if np.allclose(np.std(x), 0) and np.allclose(np.std(y), 0):
        return None

    cov = np.cov(x, y)
    if cov.shape != (2, 2):
        return None
    if cov[0, 0] <= 0 or cov[1, 1] <= 0:
        return None

    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    pearson = np.clip(pearson, -1, 1)

    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)

    ellipse = Ellipse(
        (0, 0),
        width=ell_radius_x * 2,
        height=ell_radius_y * 2,
        facecolor=facecolor,
        **kwargs
    )

    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf = (transforms.Affine2D()
              .rotate_deg(45)
              .scale(scale_x, scale_y)
              .translate(mean_x, mean_y))

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


def _load_metric_csv(csv_path, value_col):
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path, usecols=['time', value_col])
        df['time'] = pd.to_numeric(df['time'], errors='coerce')
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        df = df.dropna(subset=['time', value_col])
        if df.empty:
            return pd.DataFrame()

        # Keep per-sample rows; bucket to integer seconds later
        df['time'] = df['time'].astype(float).astype(int)
        df = df.set_index('time')
        return df
    except Exception as e:
        print(f"Failed reading {csv_path}: {e}")
        return pd.DataFrame()


def data_to_exp11_df(root_path, experiment, protocols, flow_batches, runs):
    results = []

    for protocol in protocols:
        for flow_batch in flow_batches:
            util_list = []
            delay_list = []

            for run in runs:
                base_path = (
                    root_path + "/paperExperiments/" + experiment + "/csvs/" +
                    protocol + "/" + str(flow_batch) + "flows/" + str(BASE_RTT_MS) + "ms/run" + str(run)
                )

                # ---- Aggregate goodput across all servers (Mbps) ----
                # Average each flow per second first, then average across time
                per_flow_goodput_means = []
                for i in range(flow_batch):
                    gp_path = base_path + "/singledumbbell.server[" + str(i) + "].app[0]/goodput.csv"
                    df_gp = _load_metric_csv(gp_path, 'goodput')
                    if df_gp.empty:
                        per_flow_goodput_means.append(0.0)
                        continue

                    sl = df_gp.loc[EVAL_START:EVAL_END, 'goodput']
                    if sl.empty:
                        per_flow_goodput_means.append(0.0)
                    else:
                        sl_sec = sl.groupby(sl.index).mean()
                        per_flow_goodput_means.append(sl_sec.mean() / 1_000_000.0)  # bps -> Mbps

                agg_goodput_mbps = np.sum(per_flow_goodput_means)
                norm_util = agg_goodput_mbps / BANDWIDTH

                # ---- Mean RTT across all clients (ms) ----
                # Average RTT per second first (equal weight per second), then across flows
                per_flow_rtt_means = []
                for i in range(flow_batch):
                    rtt_path = base_path + "/singledumbbell.client[" + str(i) + "].tcp.conn/rtt.csv"
                    df_rtt = _load_metric_csv(rtt_path, 'rtt')
                    if df_rtt.empty:
                        continue

                    sl = df_rtt.loc[EVAL_START:EVAL_END, 'rtt']
                    if sl.empty:
                        continue

                    sl_sec = sl.groupby(sl.index).mean()
                    mean_rtt_val = sl_sec.mean()

                    # Heuristic unit handling
                    if mean_rtt_val < 5:
                        mean_rtt_ms = mean_rtt_val * 1000.0
                    else:
                        mean_rtt_ms = mean_rtt_val

                    per_flow_rtt_means.append(mean_rtt_ms)

                if len(per_flow_rtt_means) == 0:
                    norm_delay = np.nan
                else:
                    mean_rtt_ms_all_flows = float(np.mean(per_flow_rtt_means))
                    norm_delay = mean_rtt_ms_all_flows / float(BASE_RTT_MS)

                if not np.isnan(norm_delay):
                    util_list.append(norm_util)
                    delay_list.append(norm_delay)

                print(protocol, flow_batch, run, "norm_util=", norm_util, "norm_delay=", norm_delay)

            if len(util_list) == 0 or len(delay_list) == 0:
                util_mean = np.nan
                util_std = np.nan
                delay_mean = np.nan
                delay_std = np.nan
                util_arr = np.asarray([], dtype=np.float32)
                delay_arr = np.asarray([], dtype=np.float32)
            else:
                util_mean = float(np.mean(util_list))
                util_std = float(np.std(util_list))
                delay_mean = float(np.mean(delay_list))
                delay_std = float(np.std(delay_list))
                util_arr = np.asarray(util_list, dtype=np.float32)
                delay_arr = np.asarray(delay_list, dtype=np.float32)

            results.append([
                protocol, flow_batch,
                util_mean, util_std,
                delay_mean, delay_std,
                util_arr, delay_arr
            ])

    columns = [
        'protocol', 'flow_batch',
        'norm_util_mean', 'norm_util_std',
        'norm_delay_mean', 'norm_delay_std',
        'norm_util_list', 'norm_delay_list'
    ]
    return pd.DataFrame(results, columns=columns)


def plot_exp11_scatter_norm_util_vs_norm_delay(df):
    # Taller figure + explicit top margin for protocol legend
    fig, ax = plt.subplots(figsize=(5.5, 2))
    ax.grid(True, which="major", alpha=0.2, linewidth=0.6)
    for prot in PROTOCOLS:
        for fb in FLOW_BATCHES:
            sub_df = df[(df['protocol'] == prot) & (df['flow_batch'] == fb)]
            if sub_df.empty:
                continue

            row = sub_df.iloc[0]
            x_runs = row['norm_delay_list']
            y_runs = row['norm_util_list']

            if isinstance(x_runs, np.ndarray) and isinstance(y_runs, np.ndarray):
                if len(x_runs) >= 2 and len(y_runs) >= 2:
                    confidence_ellipse(
                        x_runs, y_runs, ax,
                        facecolor=COLORS_LEO.get(prot, 'gray'),
                        alpha=0.25,
                        edgecolor='none'
                    )

            ax.scatter(
                row['norm_delay_mean'],
                row['norm_util_mean'],
                marker=MARKERS_BATCH.get(fb, 'o'),
                s=55,
                facecolors='none',
                edgecolors=COLORS_LEO.get(prot, 'gray'),
                linewidths=1.1
            )

    # Protocol legend (TOP, no frame) -- use figure legend so it won't get clipped by axes
    proto_order = ['cubic', 'bbr', 'bbr3', 'satcp', 'leocc', 'orbtcp']
    proto_labels = ['Cubic', 'BBRv1', 'BBRv3', 'SaTCP', 'LeoCC', 'OrbCC']
    proxy_lines = [Line2D([0], [0], color=COLORS_LEO[p], lw=1.5) for p in proto_order]

    fig.legend(
        proxy_lines, proto_labels,
        ncol=6,
        loc='upper center',
        bbox_to_anchor=(0.56, 0.92),
        fontsize='small',
        columnspacing=1.0,
        handletextpad=0.5,
        frameon=False
    )

    # Flow-batch legend (BOTTOM RIGHT, no frame)
    batch_handles = [
        Line2D([0], [0], marker=MARKERS_BATCH[5], linestyle='None',
               markersize=6.5, markerfacecolor='none', markeredgecolor='black', label='5 flows'),
        Line2D([0], [0], marker=MARKERS_BATCH[10], linestyle='None',
               markersize=6.5, markerfacecolor='none', markeredgecolor='black', label='10 flows'),
        Line2D([0], [0], marker=MARKERS_BATCH[20], linestyle='None',
               markersize=6.5, markerfacecolor='none', markeredgecolor='black', label='20 flows'),
    ]
    ax.legend(
        handles=batch_handles,
        loc='lower right',
        fontsize='small',
        frameon=False,
        borderaxespad=0.3,
        handletextpad=0.4
    )

    ax.set_xlabel("Normalised Delay", fontsize="large")
    ax.set_ylabel("Norm. Goodput", fontsize="large")

    ax.set_xlim(0.8, 5.5)
    ax.set_ylim(0.8, 1.0)
    ax.invert_xaxis()
    ax.set_xticks(np.arange(1, 6.0, 0.5)) 

    # Reserve headroom for the top legend so it never gets cut off
    fig.subplots_adjust(top=0.78, left=0.13, right=0.98, bottom=0.18)
    plt.savefig("norm_util_vs_norm_delay_experiment11.pdf", dpi=1080, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    exp11_df = data_to_exp11_df(
        ROOT_PATH,
        EXPERIMENT,
        PROTOCOLS,
        FLOW_BATCHES,
        RUNS
    )
    plot_exp11_scatter_norm_util_vs_norm_delay(exp11_df)