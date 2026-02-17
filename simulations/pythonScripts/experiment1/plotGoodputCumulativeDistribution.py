#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import random
import json
import scienceplots
import subprocess
from matplotlib.lines import Line2D

if __name__ == "__main__":
    plt.style.use('science')
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = True
    plt.rcParams['axes.labelsize'] = "large"
    plt.rcParams['xtick.labelsize'] = "large"
    plt.rcParams['ytick.labelsize'] = "large"
    # plt.rcParams.update({
    #     "font.family": "serif",
    #     "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    # })
    
    BINS = 50
    runs = list(range(1, 51))
    protocols = ["orbtcp", "bbr", "cubic", "bbr3"]

    # List containing each data point (each run). Values for each datapoint: protocol, run_number, average_goodput, optimal_goodput
    rttData = []
    lossData = []

    # NO LOSS DATA
    for protocol in protocols:
        for run in runs:
            filePath = f'../../paperExperiments/experiment1/csvs/{protocol}/run{run}/singledumbbell.server[0].app[0]/goodput.csv'
            if os.path.exists(filePath):
                # BANDWIDTH
                with open(f'../../paperExperiments/bandwidths/experiment1/run{run}.json') as jsonData:
                    d = json.load(jsonData)

                floatD = {float(k): float(v) for k, v in d.items()}
                time, data = np.genfromtxt(filePath, dtype=float, delimiter=',', skip_header=1).transpose()
                bwResults = data

                optimalBandwidthY = np.array(list(floatD.values()))
                optimalBandwidthMean = np.mean(optimalBandwidthY)

                # GOODPUT
                rttData.append([protocol, run, bwResults.mean() * 0.000001, optimalBandwidthMean])  # bytes to Mbps

    # LOSS DATA
    for protocol in protocols:
        for run in runs:
            filePath2 = f'../../paperExperiments/experiment2/csvs/{protocol}/run{run}/singledumbbell.server[0].app[0]/goodput.csv'
            if os.path.exists(filePath2):
                # BANDWIDTH
                with open(f'../../paperExperiments/bandwidths/experiment2/run{run}.json') as jsonData:
                    d = json.load(jsonData)

                floatD = {float(k): float(v) for k, v in d.items()}
                time2, data2 = np.genfromtxt(filePath2, dtype=float, delimiter=',', skip_header=1).transpose()
                bwResults2 = data2

                optimalBandwidthY2 = np.array(list(floatD.values()))
                optimalBandwidthMean2 = np.mean(optimalBandwidthY2)

                # GOODPUT
                lossData.append([protocol, run, bwResults2.mean() * 0.000001, optimalBandwidthMean2])

    # Convert to DataFrame
    bw_rtt_data = pd.DataFrame(rttData, columns=['protocol', 'run_number', 'average_goodput', 'optimal_goodput'])
    loss_data = pd.DataFrame(lossData, columns=['protocol', 'run_number', 'average_goodput', 'optimal_goodput'])

    # Color mapping
    colours = {'cubic': '#0C5DA5', 'bbr': '#00B945', 'orbtcp': '#FF9500', 'bbr3': '#eb0909'}

    # Plot
    fig, ax = plt.subplots(figsize=(3, 1.5))

    optimals = bw_rtt_data[bw_rtt_data['protocol'] == 'bbr']['optimal_goodput']
    values, base = np.histogram(optimals, bins=BINS)
    cumulative = np.cumsum(values)
    ax.plot(base[:-1], cumulative / 50 * 100, c='black')

    for protocol in protocols:
        # RTT (no loss)
        avg_goodputs = bw_rtt_data[bw_rtt_data['protocol'] == protocol]['average_goodput']
        values, base = np.histogram(avg_goodputs, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / 50 * 100, label=f"{protocol}-rtt", c=colours[protocol])

        # Loss
        avg_goodputs = loss_data[loss_data['protocol'] == protocol]['average_goodput']
        values, base = np.histogram(avg_goodputs, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / 50 * 100, label=f"{protocol}-loss", c=colours[protocol], linestyle='dashed')

    ax.set_xlabel("Average Goodput (Mbps)")
    ax.set_ylabel("Percent of Trials (\%)")

    # -------------------------------
    # Separate legends
    # -------------------------------

    protocol_label_map = {
        'orbtcp': 'OrbTCP',
        'bbr': 'BBRv1',
        'cubic': 'Cubic',
        'bbr3': 'BBRv3'
    }

    protocol_legend_handles = [
        Line2D([0], [0], color='black', lw=1.5, label='Optimal')
    ] + [
        Line2D([0], [0], color=colours[protocol], lw=1.5, label=protocol_label_map[protocol])
        for protocol in protocols
    ]

    # Line style legend (RTT vs Loss)
    style_legend_handles = [
        Line2D([0], [0], color='black', linestyle='solid', lw=1.5, label='bw-rtt'),
        Line2D([0], [0], color='black', linestyle='dashed', lw=1.5, label='bw-rtt-loss')
    ]

    # Add protocol legend
    # fig.legend(handles=protocol_legend_handles,
    #         ncol=3,  # 3 per row, so you get 2 rows
    #         loc='upper center',
    #         bbox_to_anchor=(0.5, 1.15),  # center position
    #         columnspacing=1.5,           # more spacing
    #         handletextpad=0.6,
    #         handlelength=1.2,
    #         fontsize='small')

    # Add style legend (inside plot, top left)
    ax.legend(handles=style_legend_handles,
          loc='upper left',
          bbox_to_anchor=(0.06, 1.0),
          fontsize='x-small')
    
    plt.subplots_adjust(top=1)
    # Save
    for format in ['pdf']:
        fig.savefig(f"joined_goodput_cdf.{format}", dpi=1080, bbox_inches='tight')