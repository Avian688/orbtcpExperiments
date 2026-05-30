#!/usr/bin/env python3

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
from pathlib import Path
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plotDataExport import build_cdf_points, export_plot_dataframe
from plotProtocolSupport import EXPERIMENT_1_PROTOCOLS, PROTOCOL_COLORS, PROTOCOL_LABELS

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

    protocols = EXPERIMENT_1_PROTOCOLS

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

    colours = PROTOCOL_COLORS

    fig, ax = make_cdf_axes("Average Goodput (Mbps)", show_ylabel=True)
    cdf_exports = []

    # "Optimal" curve: use optimal_goodput distribution (kept as original behaviour)
    optimals = bw_rtt_data[bw_rtt_data["protocol"] == "bbr"]["optimal_goodput"]
    optimal_cdf = build_cdf_points(optimals, BINS, denominator=50)
    ax.plot(optimal_cdf["x"], optimal_cdf["y_percent_trials"], c="black")
    cdf_exports.append(optimal_cdf.assign(series="Optimal", protocol="optimal", scenario="bw-rtt"))

    for protocol in protocols:
        # RTT (no loss)
        avg_goodputs = bw_rtt_data[bw_rtt_data["protocol"] == protocol]["average_goodput"]
        cdf = build_cdf_points(avg_goodputs, BINS, denominator=50)
        ax.plot(cdf["x"], cdf["y_percent_trials"], c=colours[protocol])
        cdf_exports.append(cdf.assign(series=PROTOCOL_LABELS[protocol], protocol=protocol, scenario="bw-rtt"))

        # Loss
        avg_goodputs = loss_data[loss_data["protocol"] == protocol]["average_goodput"]
        cdf = build_cdf_points(avg_goodputs, BINS, denominator=50)
        ax.plot(cdf["x"], cdf["y_percent_trials"], c=colours[protocol], linestyle="dashed")
        cdf_exports.append(cdf.assign(series=PROTOCOL_LABELS[protocol], protocol=protocol, scenario="bw-rtt-loss"))

    #ax.set_xlabel("Average Goodput (Mbps)")
    #ax.set_ylabel("\% of Trials")

    protocol_label_map = PROTOCOL_LABELS

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
    # ax.legend(
    #     handles=style_legend_handles,
    #     loc="upper left",
    #     bbox_to_anchor=(0.06, 1.0),
    #     fontsize="x-small",
    # )

    plt.subplots_adjust(top=1)

    if cdf_exports:
        export_plot_dataframe(
            "joined_goodput_cdf_points.csv",
            pd.concat(cdf_exports, ignore_index=True).rename(columns={"x": "average_goodput_mbps"}),
            metadata={
                "experiment": "experiment1_and_2",
                "plot": "joined_goodput_cdf",
                "description": "Final CDF points plotted for average goodput; experiment2 is represented by bw-rtt-loss.",
            },
        )
    export_plot_dataframe(
        "joined_goodput_cdf_run_summary.csv",
        pd.concat([
            bw_rtt_data.assign(scenario="bw-rtt"),
            loss_data.assign(scenario="bw-rtt-loss"),
        ], ignore_index=True),
        metadata={
            "experiment": "experiment1_and_2",
            "plot": "joined_goodput_cdf",
            "description": "Per-run average goodput values used to build the plotted CDF points.",
        },
    )

    for format in ["pdf"]:
        fig.savefig(f"joined_goodput_cdf.{format}", dpi=1080, bbox_inches="tight", pad_inches=0.02)
