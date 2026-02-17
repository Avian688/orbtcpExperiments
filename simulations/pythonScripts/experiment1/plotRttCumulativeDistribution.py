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
            filePath = f'../../paperExperiments/experiment1/csvs/{protocol}/run{run}/singledumbbell.client[0].tcp.conn/rtt.csv'
            if os.path.exists(filePath):
                with open(f'../../paperExperiments/baseRtts/experiment1/run{run}.json') as jsonData:
                    base_rtts = json.load(jsonData)

                # Convert base RTTs from ms to seconds
                float_base_rtts = {float(k): float(v) for k, v in base_rtts.items()}
                time, data = np.genfromtxt(filePath, dtype=float, delimiter=',', skip_header=1).transpose()
                
                df1 = pd.DataFrame({'time': time, 'rtt': data})
                df1['second'] = df1['time'].astype(int)
                per_second_avg1 = df1.groupby('second')['rtt'].mean()
                # # Clip RTTs to not go below corresponding base RTT
                # corrected_rtts = []
                # for t, rtt in zip(time, data):
                #     nearest_base_time = min(float_base_rtts.keys(), key=lambda x: abs(x - t))
                #     base_rtt = float_base_rtts[nearest_base_time]
                #     corrected_rtts.append(max(rtt, base_rtt))

                # Use unmodified optimal RTTs (still in ms)
                optimalRttMean = np.mean(list(base_rtts.values()))
                rttData.append([protocol, run, per_second_avg1.mean()*1000, optimalRttMean])

    # LOSS DATA
    # for protocol in protocols:
    #     for run in runs:
    #         filePath2 = f'../../paperExperiments/experiment2/csvs/{protocol}/run{run}/singledumbbell.client[0].tcp.conn/rtt.csv'
    #         if os.path.exists(filePath2):
    #             with open(f'../../paperExperiments/baseRtts/experiment1/run{run}.json') as jsonData:
    #                 base_rtts2 = json.load(jsonData)

    #             # Convert base RTTs from ms to seconds
    #             float_base_rtts2 = {float(k): float(v) for k, v in base_rtts2.items()}
    #             time2, data2 = np.genfromtxt(filePath2, dtype=float, delimiter=',', skip_header=1).transpose()

    #             df2 = pd.DataFrame({'time': time2, 'rtt': data2})
    #             df2['second'] = df2['time'].astype(int)
    #             per_second_avg2 = df2.groupby('second')['rtt'].mean()

    #             # corrected_rtts2 = []
    #             # for t, rtt in zip(time2, data2):
    #             #     nearest_base_time = min(float_base_rtts2.keys(), key=lambda x: abs(x - t))
    #             #     base_rtt2 = float_base_rtts2[nearest_base_time]
    #             #     corrected_rtts2.append(max(rtt, base_rtt2))

    #             # Use unmodified optimal RTTs (still in ms)
    #             optimalRttMean2 = np.mean(list(base_rtts2.values()))
    #             lossData.append([protocol, run, per_second_avg2.mean()*1000, optimalRttMean2])

    # Convert to DataFrame
    bw_rtt_data = pd.DataFrame(rttData, columns=['protocol', 'run_number', 'average_rtt', 'optimal_rtt'])
    #loss_data = pd.DataFrame(lossData, columns=['protocol', 'run_number', 'average_rtt', 'optimal_rtt'])

    # Color mapping
    colours = {'cubic': '#0C5DA5', 'bbr': '#00B945', 'orbtcp': '#FF9500', 'bbr3': '#eb0909'}

    # Plot
    fig, ax = plt.subplots(figsize=(3, 1.5))

    optimals = bw_rtt_data[bw_rtt_data['protocol'] == 'bbr']['optimal_rtt']
    values, base = np.histogram(optimals, bins=BINS)
    cumulative = np.cumsum(values)
    ax.plot(base[:-1], cumulative / 50 * 100, c='black')

    for protocol in protocols:
        # RTT (no loss)
        avg_rtts = bw_rtt_data[bw_rtt_data['protocol'] == protocol]['average_rtt']
        values, base = np.histogram(avg_rtts, bins=BINS)
        cumulative = np.cumsum(values)
        ax.plot(base[:-1], cumulative / 50 * 100, label=f"{protocol}-rtt", c=colours[protocol])
        
        # Loss
        # avg_rtts = loss_data[loss_data['protocol'] == protocol]['average_rtt']
        # values, base = np.histogram(avg_rtts, bins=BINS)
        # cumulative = np.cumsum(values)
        # ax.plot(base[:-1], cumulative / 50 * 100, label=f"{protocol}-loss", c=colours[protocol], linestyle='dashed')

    #ax.set(xlabel="Average RTT (ms)")
    #ax.set_xlabel("Average RTT (ms)", fontsize="large")
    ax.set_xlabel("Average RTT (ms)")
    # -------------------------------
    # Separate legends
    # -------------------------------

    protocol_label_map = {
        'orbtcp': 'LeoTCP',
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
        Line2D([0], [0], color='black', linestyle='solid', lw=1.5, label='bw-rtt')
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
        fig.savefig(f"joined_rtt_cdf.{format}", dpi=1080, bbox_inches='tight')