#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
from matplotlib.lines import Line2D

def make_cdf_axes(xlabel, show_ylabel=True):
    fig = plt.figure(figsize=(5, 2))
    # Fixed axes rectangle -> identical plotting box in every output
    ax = fig.add_axes([0.16, 0.28, 0.82, 0.66])

    ax.set_xlabel(xlabel)
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 50, 100])

    # Reserve identical left margin space in every plot
    if show_ylabel:
        ax.set_ylabel(r"\% of Trials")

    return fig, ax

if __name__ == "__main__":
    plt.style.use("science")
    pd.set_option("display.max_rows", None)
    plt.rcParams["text.usetex"] = True
    plt.rcParams["axes.labelsize"] = "large"
    plt.rcParams["xtick.labelsize"] = "large"
    plt.rcParams["ytick.labelsize"] = "large"

    BINS = 50
    runs = list(range(1, 51))
    SIM_SECONDS = 300  # simulation length

    # Same protocols as your other plots
    protocols = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"]

    retransData = []

    # NO LOSS DATA (experiment 1)
    for protocol in protocols:
        for run in runs:
            filePath = (
                f"../../paperExperiments/experiment1/csvs/{protocol}/run{run}/"
                "singledumbbell.client[0].tcp.conn/retransmissionRate.csv"
            )

            if os.path.exists(filePath):
                arr = np.genfromtxt(filePath, dtype=float, delimiter=",", skip_header=1)

                # Empty file -> assume zero retransmission throughout run
                if arr.size == 0:
                    retransData.append([protocol, run, 0.0])
                    continue

                # Handle single-row vs multi-row files
                if arr.ndim == 1:
                    if len(arr) < 2:
                        retransData.append([protocol, run, 0.0])
                        continue
                    time_vals = np.array([arr[0]], dtype=float)
                    data = np.array([arr[1]], dtype=float)
                else:
                    time_vals, data = arr.transpose()

                # Build DataFrame like your RTT script
                df1 = pd.DataFrame({"time": time_vals, "retrans": data})
                df1 = df1.sort_values("time").reset_index(drop=True)

                # Reconstruct per-second retransmission rate correctly for removeRepeats:
                # value at time t_i applies until next change time (or sim end)
                per_second_vals = np.zeros(SIM_SECONDS, dtype=float)  # bytes/s for seconds 0..299

                # Defensive filtering
                df1 = df1[(df1["time"] >= 0) & (df1["time"] <= SIM_SECONDS)]

                if not df1.empty:
                    times = df1["time"].to_numpy(dtype=float)
                    vals = df1["retrans"].to_numpy(dtype=float)

                    for i in range(len(times)):
                        start_t = times[i]
                        end_t = times[i + 1] if i + 1 < len(times) else SIM_SECONDS

                        # Fill integer seconds whose interval [s, s+1) lies under this step value.
                        # Since your metric is sampled every second and removeRepeats compresses repeats,
                        # this recreates the per-second series for averaging.
                        start_s = int(np.floor(start_t))
                        end_s = int(np.floor(end_t))

                        start_s = max(0, start_s)
                        end_s = min(SIM_SECONDS, end_s)

                        # If next change is at 6, current value covers seconds start_s..5
                        if end_s > start_s:
                            per_second_vals[start_s:end_s] = vals[i]

                    # If first recorded time is > 0, values before it remain 0 (already correct)

                # Match your RTT script style: average of per-second averages
                # Convert bytes/s -> Mbps for plotting
                per_second_avg_mbps = (per_second_vals * 8e-6)
                retransData.append([protocol, run, per_second_avg_mbps.mean()])

    retrans_df = pd.DataFrame(
        retransData,
        columns=["protocol", "run_number", "average_retrans_mbps"]
    )

    # Colour mapping (same as your other plots)
    colours = {
        "cubic": "#0C5DA5",   # blue
        "bbr": "#00B945",     # green
        "orbtcp": "#FF9500",  # orange
        "bbr3": "#EB0909",    # red
        "satcp": "#7E2F8E",   # purple
        "leocc": "#17BECF",   # teal/cyan
    }

    fig, ax = make_cdf_axes("Average Retr. Rate (Mbps)", show_ylabel=False)

    # Plot CDFs (experiment 1 only)
    for protocol in protocols:
        avg_retrans = retrans_df[retrans_df["protocol"] == protocol]["average_retrans_mbps"]

        if avg_retrans.empty:
            print(f"[WARN] No retransmission data found for {protocol}")
            continue

        values, base = np.histogram(avg_retrans, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / len(avg_retrans) * 100, c=colours[protocol])

    #ax.set_xlabel("Average Retr. Rate (Mbps)")
    #ax.set_ylabel("\% of Trials")

    protocol_label_map = {
        "orbtcp": "OrbCC",
        "bbr": "BBRv1",
        "cubic": "Cubic",
        "bbr3": "BBRv3",
        "satcp": "SatCP",
        "leocc": "LeoCC",
    }

    protocol_legend_handles = [
        Line2D([0], [0], color=colours[p], lw=1.5, label=protocol_label_map[p])
        for p in protocols
    ]

    # ax.legend(
    #     handles=protocol_legend_handles,
    #     loc="lower center",          # anchor the *bottom* of legend
    #     bbox_to_anchor=(0.5, 1),  # x=center, y=above axes (increase y to move higher)
    #     ncol=4,                      # 8 items -> 2 rows of 4 (adjust if needed)
    #     fontsize="x-small",
    # )
    
    plt.subplots_adjust(top=1)

    for format in ["pdf"]:
        fig.savefig(f"joined_retransmissions_cdf.{format}", dpi=1080, bbox_inches="tight", pad_inches=0.02)#, bbox_inches="tight")