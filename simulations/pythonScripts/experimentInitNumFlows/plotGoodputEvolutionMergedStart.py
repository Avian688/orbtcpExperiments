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
num_servers = 50   # only first 50 flows
num_runs    = 5

LINEWIDTH   = 0.30
COLOR       = "tab:blue"

# time grid: 0–10 seconds, integer
times = np.arange(0, 11)

for protocol in protocols:
    # collect per‐flow times → list of Mbps values over runs
    flow_time = {i: {} for i in range(num_servers)}

    # read all runs
    for run in range(1, num_runs + 1):
        run_path = os.path.join(base_dir, protocol, buffer, delay, f"run{run}")
        for i in range(num_servers):
            fp = os.path.join(
                run_path,
                f"singledumbbell.server[{i}].app[0]",
                "goodput.csv"
            )
            if not os.path.exists(fp):
                continue

            df = pd.read_csv(fp)
            df["time"]    = df["time"].round().astype(int)
            df["goodput"] = df["goodput"].astype(float) / 1e6  # → Mbps
            for t, g in zip(df["time"], df["goodput"]):
                if 0 <= t <= 10:
                    flow_time[i].setdefault(int(t), []).append(g)

    # ensure each flow has a zero at t=0
    for tdict in flow_time.values():
        tdict.setdefault(0, [0])

    # compute per‐flow mean series on 0–10s grid
    flow_mean = {
        i: [np.mean(flow_time[i].get(t, [0])) for t in times]
        for i in range(num_servers)
    }

    # compute merged variance envelope across flows
    min_vals = [min(flow_mean[i][idx] for i in range(num_servers)) for idx in range(len(times))]
    max_vals = [max(flow_mean[i][idx] for i in range(num_servers)) for idx in range(len(times))]

    # plot
    plt.figure(figsize=(3, 1.5))
    # individual flows
    for i in range(num_servers):
        plt.plot(times, flow_mean[i],
                 linewidth=LINEWIDTH,
                 color=COLOR,
                 alpha=0.8)
    # merged variance shading
    plt.fill_between(times, min_vals, max_vals,
                     color=COLOR,
                     alpha=0.2)

    # axes
    plt.ylim(0, 12)
    plt.xlim(0, 10)
    # generate ticks at [10, 20, 30, 40, 50]
    ticks = [10, 20, 30, 40, 50]
    plt.xticks(ticks, [str(t) for t in ticks])

    plt.xlabel("Time (s)")
    plt.ylabel("Goodput (Mbps)")

    # save
    out_name = f"{protocol}_first10s_50flows.png"
    plt.savefig(out_name, dpi=1080)
    plt.close()