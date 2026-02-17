import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
# Use science-style plots
plt.style.use("science")
plt.rcParams['text.usetex'] = False

# Constants
base_dir    = "../../../paperExperiments/experimentInitNumFlows/csvs"
protocols   = ["Orbtcp", "OrbtcpNoInitFlows", "OrbtcpNoSharedFlows"]
buffer      = "mediumbuffer"
delay       = "100ms"
num_servers = 65
num_runs    = 5

LINEWIDTH   = 0.30

colors = {
    "Orbtcp":              "tab:blue",
    "OrbtcpNoInitFlows":   "tab:orange",
    "OrbtcpNoSharedFlows": "tab:green"
}

# forced start times for flows 50..64: 1×10s, 2×20s, 4×30s, 8×40s
late_starts = [10] + [20]*2 + [30]*4 + [40]*8  # len = 15

for protocol in protocols:
    # collect per-flow times → list of Mbps values over runs
    flow_time = {i: {} for i in range(num_servers)}

    # read all runs
    for run in range(1, num_runs+1):
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

    # skip if no data at all
    if not any(flow_time[i] for i in flow_time):
        print(f"No data for {protocol}")
        continue

    plt.figure(figsize=(3, 1.5))

    for i, tdict in flow_time.items():
        if not tdict:
            continue

        # sorted times and per-time stats
        orig_t    = sorted(tdict.keys())
        mean_vals = [sum(tdict[t]) / len(tdict[t]) for t in orig_t]
        min_vals  = [min(tdict[t]) for t in orig_t]
        max_vals  = [max(tdict[t]) for t in orig_t]

        # compute where to put the zero‐Mbps marker:
        #  - flows 0–49: at their actual first time orig_t[0] (usually 0 s)
        #  - flows 50–64: at the forced times [10,20,30,40]
        if i < 50:
            t0 = orig_t[0]
        else:
            t0 = late_starts[i - 50]

        # prepend the (t0, 0) point
        times = [t0]      + orig_t
        means = [0.0]     + mean_vals
        mins  = [0.0]     + min_vals
        maxs  = [0.0]     + max_vals

        plt.plot(times, means,
                 linewidth=LINEWIDTH,
                 color=colors[protocol],
                 alpha=0.8)
        plt.fill_between(times, mins, maxs,
                         color=colors[protocol],
                         alpha=0.2)

    # force y-axis baseline at 0; x from 0–50
    plt.ylim(0, 12)
    plt.xlim(0, 50)
    plt.xticks([10, 20, 30, 40, 50], ["10", "20", "30", "40", "50"])

    plt.xlabel("Time (s)")
    plt.ylabel("Goodput (Mbps)")

    plt.savefig(f"{protocol}_perflow_goodput.png", dpi=1080)
    plt.close()