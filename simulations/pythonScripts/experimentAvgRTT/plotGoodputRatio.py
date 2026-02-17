import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
from matplotlib.ticker import ScalarFormatter
from matplotlib.lines import Line2D

# Use science‐style plots
plt.style.use("science")
plt.rcParams['text.usetex'] = True
plt.rcParams['axes.labelsize'] = "medium"
plt.rcParams['xtick.labelsize'] = "medium"
plt.rcParams['ytick.labelsize'] = "medium"

# Constants
PROTOCOLS = ["orbtcp", "orbtcpNoAvgRTT"]
BWS       = [100]
DELAYS    = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
RUNS      = [1, 2, 3, 4, 5]

LINEWIDTH   = 0.30
ELINEWIDTH  = 0.75
CAPTHICK    = ELINEWIDTH
CAPSIZE     = 2

# assign each protocol a color
protocol_colors = {
    "orbtcp":          "tab:orange",
    "orbtcpNoAvgRTT":  "tab:blue",
}

def plot_points_rtt(ax, df, data_col, err_col, marker, label, color):
    """Plot errorbar points for RTT vs. goodput ratio."""
    if df.empty:
        return
    x = df.index
    y = df[data_col]
    yerr = df[err_col]
    markers, caps, bars = ax.errorbar(
        x, y,
        yerr=yerr,
        marker=marker,
        color=color,
        linewidth=LINEWIDTH,
        elinewidth=ELINEWIDTH,
        capsize=CAPSIZE,
        capthick=CAPTHICK,
        label=label
    )
    for bar in bars:
        bar.set_alpha(0.5)
    for cap in caps:
        cap.set_alpha(0.5)

# Create figure & axis
fig, ax = plt.subplots(figsize=(4.5, 1.2))
ax.set_ylim(0, 1.1)
plt.margins(y=0.05)

# Gather data
records = []
for protocol in PROTOCOLS:
    for bw in BWS:
        for delay in DELAYS:
            start_time = delay
            end_time   = 2 * delay

            totals = []
            for run in RUNS:
                base = (
                    f"../../../paperExperiments/"
                    f"experimentAvgRTT/csvs/{protocol}/"
                    f"mediumbuffer/{delay}ms/run{run}/"
                )
                p1 = base + "singledumbbell.server[0].app[0]/goodput.csv"
                p2 = base + "singledumbbell.server[1].app[0]/goodput.csv"

                if os.path.exists(p1) and os.path.exists(p2):
                    r1 = pd.read_csv(p1)
                    r2 = pd.read_csv(p2)
                    r1['time'] = r1['time'].astype(float).astype(int)
                    r2['time'] = r2['time'].astype(float).astype(int)

                    # filter by interval and set index
                    mask1 = (r1['time'] > start_time) & (r1['time'] < end_time)
                    mask2 = (r2['time'] > start_time) & (r2['time'] < end_time)
                    r1 = r1[mask1].drop_duplicates('time').set_index('time')
                    r2 = r2[mask2].drop_duplicates('time').set_index('time')

                    total = r1.join(r2, how='inner', lsuffix='1', rsuffix='2').dropna()
                    if not total.empty:
                        ratios = (total.min(axis=1) / total.max(axis=1)).values
                        totals.append(ratios)
                else:
                    print(f"Missing files for run {run}: {p1}, {p2}")

            if totals:
                all_ratios = np.concatenate(totals)
                if all_ratios.size:
                    records.append([
                        protocol,
                        bw,
                        delay,
                        delay / 10,
                        all_ratios.mean(),
                        all_ratios.std()
                    ])

# Build DataFrame
summary = pd.DataFrame(
    records,
    columns=[
        'protocol', 'goodput', 'delay', 'delay_ratio',
        'goodput_ratio_mean', 'goodput_ratio_std'
    ]
)

# Plot each protocol's curve
for protocol, marker in zip(PROTOCOLS, ['x', '.']):
    dfp   = summary[summary['protocol'] == protocol].set_index('delay')
    label = "LeoTCP" if protocol == "orbtcp" else "LeoTCP No AvgRTT"
    color = protocol_colors[protocol]
    plot_points_rtt(
        ax, dfp,
        'goodput_ratio_mean',
        'goodput_ratio_std',
        marker, label, color
    )

# Axis labels & formatting
ax.set(
    xscale='linear',
    yscale='linear',
    xlabel='RTT (ms)',
    ylabel='Goodput Ratio'
)
for axis in (ax.xaxis, ax.yaxis):
    axis.set_major_formatter(ScalarFormatter())
    axis.get_major_formatter().set_scientific(False)

# Build legend with line+marker proxies (no variance)
markers = ['x', '.']
colors  = [protocol_colors[p] for p in PROTOCOLS]
labels  = ["LeoTCP", "LeoTCP No AvgRTT"]
proxy_lines = [
    Line2D([0], [0],
           marker=mk,
           color=col,
           linestyle='-',
           linewidth=LINEWIDTH,
           markersize=6)
    for mk, col in zip(markers, colors)
]
ax.legend(
    handles=proxy_lines,
    labels=labels,
    ncol=2,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.2),
    frameon=False,
    columnspacing=1,
    handletextpad=0.5,
    labelspacing=0.1,
    borderaxespad=0.0,
    fontsize='small'
)

# Save the figure
plt.savefig("avgrtt_goodput_ratio_combined.pdf", dpi=1080)