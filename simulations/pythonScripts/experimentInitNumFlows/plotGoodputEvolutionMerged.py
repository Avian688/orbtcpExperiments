import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
from matplotlib.ticker import ScalarFormatter
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plotDataExport import export_plot_dataframe
from plotProtocolSupport import PROTOCOL_COLORS, compact_protocol_legend_kwargs

# Use science-style plots
plt.style.use("science")
plt.rcParams['text.usetex'] = True
plt.rcParams['axes.labelsize'] = "medium"
plt.rcParams['xtick.labelsize'] = "medium"
plt.rcParams['ytick.labelsize'] = "medium"

# Constants
base_dir    = "../../../paperExperiments/experimentInitNumFlows/csvs"
protocols   = ["OrbtcpPintNoInitialPhase", "OrbtcpPint"]
buffer      = "mediumbuffer"
delay       = "100ms"
num_servers = 65
num_runs    = 5
LINEWIDTH   = 0.30
AGG_WIDTH   = LINEWIDTH * 2.5  # bolder aggregate

# Zero-offsets for the 15 “late” flows (indices 50…64)
late_starts = [10] + [20]*2 + [30]*4 + [40]*8

# Assign each protocol its own color
protocol_colors = {
    "OrbtcpPint":               PROTOCOL_COLORS["orbtcp_pint"],
    "OrbtcpPintNoInitialPhase": "tab:blue",
}

# Display names for legend
display_names = {
    "OrbtcpPint":               "OrbCC",
    "OrbtcpPintNoInitialPhase": "OrbCC without initial phase",
}

plt.figure(figsize=(4.5, 1.2))
plot_exports = []

for protocol in protocols:
    # 1) Collect per-flow times → list of Mbps values over runs
    flow_time = {i: {} for i in range(num_servers)}
    for run in range(1, num_runs + 1):
        run_path = os.path.join(base_dir, protocol, buffer, delay, f"run{run}")
        for i in range(num_servers):
            fp = os.path.join(run_path,
                              f"singledumbbell.server[{i}].app[0]",
                              "goodput.csv")
            if not os.path.exists(fp):
                continue
            df = pd.read_csv(fp)
            df["time"]    = df["time"].round().astype(int)
            df["goodput"] = df["goodput"].astype(float) / 1e6  # → Mbps
            for t, g in zip(df["time"], df["goodput"]):
                flow_time[i].setdefault(int(t), []).append(g)

    # Skip if no data
    if not any(flow_time.values()):
        print(f"No data for {protocol}")
        continue

    color = protocol_colors[protocol]

    # 2) Merge & plot first 50 flows as mean only (bolder, dashed, lower zorder)
    merged = {}
    for i in range(50):
        for t, vals in flow_time[i].items():
            merged.setdefault(t, []).extend(vals)
    merged.setdefault(0, [0])
    times     = sorted(merged.keys())
    mean_vals = [np.mean(merged[t]) for t in times]

    t_m = [0] + times
    m_m = [0] + mean_vals
    plot_exports.append(pd.DataFrame({
        "protocol": protocol,
        "series": "initial_50_flows_mean",
        "flow_index": "0-49",
        "x_time_s": t_m,
        "y_goodput_mbps": m_m,
        "y_min_goodput_mbps": np.nan,
        "y_max_goodput_mbps": np.nan,
    }))

    plt.plot(t_m, m_m,
             linewidth=AGG_WIDTH,
             linestyle='--',       # dashed on the axes
             color=color,
             zorder=1)

    # 3) Plot each of the remaining 15 flows individually with shading (solid, higher zorder)
    for i in range(50, num_servers):
        tdict = flow_time[i]
        if not tdict:
            continue
        orig_t = sorted(tdict.keys())
        mean_i = [np.mean(tdict[t]) for t in orig_t]
        min_i  = [np.min(tdict[t]) for t in orig_t]
        max_i  = [np.max(tdict[t]) for t in orig_t]

        t0    = late_starts[i - 50]
        times = [t0] + orig_t
        means = [0.0] + mean_i
        mins  = [0.0] + min_i
        maxs  = [0.0] + max_i
        plot_exports.append(pd.DataFrame({
            "protocol": protocol,
            "series": "late_flow",
            "flow_index": i,
            "x_time_s": times,
            "y_goodput_mbps": means,
            "y_min_goodput_mbps": mins,
            "y_max_goodput_mbps": maxs,
        }))

        plt.plot(times, means,
                 linewidth=LINEWIDTH,
                 color=color,
                 alpha=0.6,
                 linestyle='-',
                 zorder=2)
        plt.fill_between(times, mins, maxs,
                         color=color,
                         alpha=0.1,
                         zorder=2)

# Finalize axes
ax = plt.gca()
ax.set_ylim(0, 8)
ax.set_xlim(0, 50)
ax.set_xticks([10, 20, 30, 40, 50])
ax.set_xticklabels(["10", "20", "30", "40", "50"])
ax.set_yticks([0, 4, 8])
ax.set_xlabel("Time (s)")
ax.set_ylabel("Goodput (Mbps)")

# Use ScalarFormatter to avoid scientific notation
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.xaxis.get_major_formatter().set_scientific(False)
ax.yaxis.get_major_formatter().set_scientific(False)

# Build solid-line proxies for the legend
proxy_lines = [
    Line2D([0], [0], color=protocol_colors[p],
           linewidth=AGG_WIDTH, linestyle='-')
    for p in protocols
]
proxy_labels = [display_names[p] for p in protocols]

# Legend at top center, two columns, using proxies
plt.legend(handles=proxy_lines,
           labels=proxy_labels,
           loc='upper center',
           bbox_to_anchor=(0.5, 1.2),
           **compact_protocol_legend_kwargs(proxy_labels))

# Save only; no tight_layout or show
if plot_exports:
    export_plot_dataframe(
        "all_protocols_grouped_perflow_toplegend_scalar_points.csv",
        pd.concat(plot_exports, ignore_index=True),
        metadata={
            "experiment": "experimentInitNumFlows",
            "plot": "all_protocols_grouped_perflow_toplegend_scalar",
            "description": "Final time-series points plotted for the aggregate first-50-flow curve and late-joining per-flow curves.",
        },
    )
plt.savefig(
    "all_protocols_grouped_perflow_toplegend_scalar.pdf",
    dpi=1080,
    bbox_inches="tight",
    pad_inches=0.02,
)
