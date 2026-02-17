import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
from matplotlib.ticker import ScalarFormatter
from matplotlib.lines import Line2D

# Use science-style plots
plt.style.use("science")
plt.rcParams['text.usetex'] = True
plt.rcParams['axes.labelsize'] = "medium"
plt.rcParams['xtick.labelsize'] = "medium"
plt.rcParams['ytick.labelsize'] = "medium"

# Constants
base_dir    = "../../../paperExperiments/experimentInitNumFlows/csvs"
protocols   = ["Orbtcp", "OrbtcpNoInitFlows"]   # protocols to plot
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
    "Orbtcp":            "tab:orange",
    "OrbtcpNoInitFlows": "tab:blue",
}

# Display names for legend
display_names = {
    "Orbtcp":            "LeoTCP",
    "OrbtcpNoInitFlows": "LeoTCP No InitPhase",
}

plt.figure(figsize=(4.5, 1.2))

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
           frameon=False,
           ncol=2,
           loc='upper center',
           bbox_to_anchor=(0.5, 1.2),
           columnspacing=1.0,
           handletextpad=0.5,
           labelspacing=0.1,
           borderaxespad=0.0,
           fontsize='small')

# Save only; no tight_layout or show
plt.savefig("all_protocols_grouped_perflow_toplegend_scalar.pdf", dpi=1080)