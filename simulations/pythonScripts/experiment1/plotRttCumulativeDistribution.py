#!/usr/bin/env python3

import os
import sys
import json
import pandas as pd
import numpy as np
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

    colours = PROTOCOL_COLORS

    fig, ax = make_cdf_axes("Average RTT (ms)", show_ylabel=False)
    cdf_exports = []

    optimals = bw_rtt_data[bw_rtt_data["protocol"] == "bbr"]["optimal_rtt"]
    optimal_cdf = build_cdf_points(optimals, BINS, denominator=50)
    ax.plot(optimal_cdf["x"], optimal_cdf["y_percent_trials"], c="black")
    cdf_exports.append(optimal_cdf.assign(series="Optimal", protocol="optimal", scenario="bw-rtt"))

    for protocol in protocols:
        avg_rtts = bw_rtt_data[bw_rtt_data["protocol"] == protocol]["average_rtt"]
        cdf = build_cdf_points(avg_rtts, BINS, denominator=50)
        ax.plot(cdf["x"], cdf["y_percent_trials"], c=colours[protocol])
        cdf_exports.append(cdf.assign(series=PROTOCOL_LABELS[protocol], protocol=protocol, scenario="bw-rtt"))

    #ax.set_xlabel("Average RTT (ms)")

    protocol_label_map = PROTOCOL_LABELS

    # (kept your style legend only)
    style_legend_handles = [
        Line2D([0], [0], color="black", linestyle="solid", lw=1.5, label="bw-rtt"),
    ]

    # ax.legend(
    #     handles=style_legend_handles,
    #     loc="upper left",
    #     bbox_to_anchor=(0.06, 1.0),
    #     fontsize="x-small",
    # )

    plt.subplots_adjust(top=1)

    if cdf_exports:
        export_plot_dataframe(
            "joined_rtt_cdf_points.csv",
            pd.concat(cdf_exports, ignore_index=True).rename(columns={"x": "average_rtt_ms"}),
            metadata={
                "experiment": "experiment1",
                "plot": "joined_rtt_cdf",
                "description": "Final CDF points plotted for average RTT.",
            },
        )
    export_plot_dataframe(
        "joined_rtt_cdf_run_summary.csv",
        bw_rtt_data.assign(scenario="bw-rtt"),
        metadata={
            "experiment": "experiment1",
            "plot": "joined_rtt_cdf",
            "description": "Per-run average RTT values used to build the plotted CDF points.",
        },
    )

    for format in ["pdf"]:
        fig.savefig(f"joined_rtt_cdf.{format}", dpi=1080, bbox_inches="tight", pad_inches=0.02)#, bbox_inches="tight")
