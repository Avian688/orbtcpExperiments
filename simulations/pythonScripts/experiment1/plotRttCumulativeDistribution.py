#!/usr/bin/env python3

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
from matplotlib.lines import Line2D

if __name__ == "__main__":
    plt.style.use("science")
    pd.set_option("display.max_rows", None)
    plt.rcParams["text.usetex"] = True
    plt.rcParams["axes.labelsize"] = "large"
    plt.rcParams["xtick.labelsize"] = "large"
    plt.rcParams["ytick.labelsize"] = "large"

    BINS = 50
    runs = list(range(1, 51))

    # Added satcp + leocc
    protocols = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"]

    rttData = []

    # NO LOSS DATA (experiment 1)
    for protocol in protocols:
        for run in runs:
            filePath = (
                f"../../paperExperiments/experiment1/csvs/{protocol}/run{run}/"
                "singledumbbell.client[0].tcp.conn/rtt.csv"
            )
            if os.path.exists(filePath):
                with open(f"../../paperExperiments/baseRtts/experiment1/run{run}.json") as jsonData:
                    base_rtts = json.load(jsonData)

                time_vals, data = np.genfromtxt(
                    filePath, dtype=float, delimiter=",", skip_header=1
                ).transpose()

                df1 = pd.DataFrame({"time": time_vals, "rtt": data})
                df1["second"] = df1["time"].astype(int)
                per_second_avg1 = df1.groupby("second")["rtt"].mean()

                # Optimal RTT mean (ms)
                optimalRttMean = np.mean(list(base_rtts.values()))

                # Measured RTT mean: your rtt.csv appears to be in seconds, so convert to ms
                rttData.append([protocol, run, per_second_avg1.mean() * 1000, optimalRttMean])

    bw_rtt_data = pd.DataFrame(rttData, columns=["protocol", "run_number", "average_rtt", "optimal_rtt"])

    # Colour mapping (added satcp + leocc, same as goodput plot)
    colours = {
        "cubic": "#0C5DA5",   # blue
        "bbr": "#00B945",     # green
        "orbtcp": "#FF9500",  # orange
        "bbr3": "#EB0909",    # red
        "satcp": "#7E2F8E",   # purple
        "leocc": "#17BECF",   # teal/cyan
    }

    fig, ax = plt.subplots(figsize=(3, 1.5))

    optimals = bw_rtt_data[bw_rtt_data["protocol"] == "bbr"]["optimal_rtt"]
    values, base = np.histogram(optimals, bins=BINS)
    cumulative = np.cumsum(values)
    ax.plot(base[:-1], cumulative / 50 * 100, c="black")

    for protocol in protocols:
        avg_rtts = bw_rtt_data[bw_rtt_data["protocol"] == protocol]["average_rtt"]
        values, base = np.histogram(avg_rtts, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / 50 * 100, c=colours[protocol])

    ax.set_xlabel("Average RTT (ms)")

    protocol_label_map = {
        "orbtcp": "OrbCC",   # <-- renamed as requested
        "bbr": "BBRv1",
        "cubic": "Cubic",
        "bbr3": "BBRv3",
        "satcp": "SatCP",
        "leocc": "LeoCC",
    }

    # (kept your style legend only)
    style_legend_handles = [
        Line2D([0], [0], color="black", linestyle="solid", lw=1.5, label="bw-rtt"),
    ]

    ax.legend(
        handles=style_legend_handles,
        loc="upper left",
        bbox_to_anchor=(0.06, 1.0),
        fontsize="x-small",
    )

    plt.subplots_adjust(top=1)

    for format in ["pdf"]:
        fig.savefig(f"joined_rtt_cdf.{format}", dpi=1080, bbox_inches="tight")