#!/usr/bin/env python3

import os
import json
import numpy as np
import pandas as pd
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
    lossData = []

    # NO LOSS DATA (experiment 1)
    for protocol in protocols:
        for run in runs:
            filePath = f"../../paperExperiments/experiment1/csvs/{protocol}/run{run}/singledumbbell.server[0].app[0]/goodput.csv"
            if os.path.exists(filePath):
                with open(f"../../paperExperiments/bandwidths/experiment1/run{run}.json") as jsonData:
                    d = json.load(jsonData)

                floatD = {float(k): float(v) for k, v in d.items()}
                time_vals, data = np.genfromtxt(filePath, dtype=float, delimiter=",", skip_header=1).transpose()
                bwResults = data

                optimalBandwidthY = np.array(list(floatD.values()))
                optimalBandwidthMean = np.mean(optimalBandwidthY)

                rttData.append([protocol, run, bwResults.mean() * 0.000001, optimalBandwidthMean])

    # LOSS DATA (experiment 2)
    for protocol in protocols:
        for run in runs:
            filePath2 = f"../../paperExperiments/experiment2/csvs/{protocol}/run{run}/singledumbbell.server[0].app[0]/goodput.csv"
            if os.path.exists(filePath2):
                with open(f"../../paperExperiments/bandwidths/experiment2/run{run}.json") as jsonData:
                    d = json.load(jsonData)

                floatD = {float(k): float(v) for k, v in d.items()}
                time_vals2, data2 = np.genfromtxt(filePath2, dtype=float, delimiter=",", skip_header=1).transpose()
                bwResults2 = data2

                optimalBandwidthY2 = np.array(list(floatD.values()))
                optimalBandwidthMean2 = np.mean(optimalBandwidthY2)

                lossData.append([protocol, run, bwResults2.mean() * 0.000001, optimalBandwidthMean2])

    bw_rtt_data = pd.DataFrame(rttData, columns=["protocol", "run_number", "average_goodput", "optimal_goodput"])
    loss_data = pd.DataFrame(lossData, columns=["protocol", "run_number", "average_goodput", "optimal_goodput"])

    # Colour mapping (added satcp + leocc)
    # Picked distinct, readable colours that don't clash with existing ones.
    colours = {
        "cubic": "#0C5DA5",   # blue
        "bbr": "#00B945",     # green
        "orbtcp": "#FF9500",  # orange
        "bbr3": "#EB0909",    # red
        "satcp": "#7E2F8E",   # purple
        "leocc": "#17BECF",   # teal/cyan
    }

    fig, ax = plt.subplots(figsize=(3, 1.5))

    # "Optimal" curve: use optimal_goodput distribution (kept as original behaviour)
    optimals = bw_rtt_data[bw_rtt_data["protocol"] == "bbr"]["optimal_goodput"]
    values, base = np.histogram(optimals, bins=BINS)
    cumulative = np.cumsum(values)
    ax.plot(base[:-1], cumulative / 50 * 100, c="black")

    for protocol in protocols:
        # RTT (no loss)
        avg_goodputs = bw_rtt_data[bw_rtt_data["protocol"] == protocol]["average_goodput"]
        values, base = np.histogram(avg_goodputs, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / 50 * 100, c=colours[protocol])

        # Loss
        avg_goodputs = loss_data[loss_data["protocol"] == protocol]["average_goodput"]
        values, base = np.histogram(avg_goodputs, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / 50 * 100, c=colours[protocol], linestyle="dashed")

    ax.set_xlabel("Average Goodput (Mbps)")
    ax.set_ylabel("Percent of Trials (\%)")

    protocol_label_map = {
        "orbtcp": "OrbCC",
        "bbr": "BBRv1",
        "cubic": "Cubic",
        "bbr3": "BBRv3",
        "satcp": "SatCP",
        "leocc": "LeoCC",
    }

    # Protocol legend (optional)
    protocol_legend_handles = [
        Line2D([0], [0], color="black", lw=1.5, label="Optimal")
    ] + [
        Line2D([0], [0], color=colours[p], lw=1.5, label=protocol_label_map[p])
        for p in protocols
    ]

    # Line style legend (RTT vs Loss)
    style_legend_handles = [
        Line2D([0], [0], color="black", linestyle="solid", lw=1.5, label="bw-rtt"),
        Line2D([0], [0], color="black", linestyle="dashed", lw=1.5, label="bw-rtt-loss"),
    ]

    # Keep your current style legend placement
    ax.legend(
        handles=style_legend_handles,
        loc="upper left",
        bbox_to_anchor=(0.06, 1.0),
        fontsize="x-small",
    )

    plt.subplots_adjust(top=1)

    for format in ["pdf"]:
        fig.savefig(f"joined_goodput_cdf.{format}", dpi=1080, bbox_inches="tight")