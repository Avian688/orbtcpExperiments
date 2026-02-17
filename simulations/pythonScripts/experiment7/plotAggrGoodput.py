import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.transforms import offset_copy
import scienceplots
plt.style.use('science')
import os, sys
from matplotlib.ticker import ScalarFormatter
import numpy as np
from matplotlib.lines import Line2D

plt.rcParams['text.usetex'] = False

BW = 100
DELAY = 50
INTERRUPTS = [20, 40 , 60, 80, 100, 120, 140, 160, 180, 200]
QMULTS = [0.2,1,4]
QMULTDICT = {0.2 : "smallbuffer", 1 : "mediumbuffer", 4 : "largebuffer" }
PROTOCOLS = ['cubic', 'bbr', 'bbr3', 'orbtcp']
RUNS = [1, 2, 3, 4, 5]

PROTOCOLS_MARKERS_LEO = {'cubic':'x','bbr':'.','orbtcp':'^','bbr3':'_'}
COLORS_LEO           = {'cubic':'#0C5DA5','bbr':'#00B945','orbtcp':'#FF9500','bbr3':'#eb0909'}
PROTOCOLS_FRIENDLY_NAME_LEO ={'cubic':'Cubic','bbr':'BBRv1','orbtcp':'LeoTCP','bbr3':'BBRv3'}

LINEWIDTH = 0.30
ELINEWIDTH = 0.75
CAPTHICK = ELINEWIDTH
CAPSIZE  = 2

def plot_points(ax, df, data, error, marker, color, label):
    if df.empty: return
    x = df.index
    y = df[data]
    yerr = df[error]
    markers, caps, bars = ax.errorbar(
        x, y, yerr=yerr,
        marker=marker,
        linewidth=LINEWIDTH,
        elinewidth=ELINEWIDTH,
        capsize=CAPSIZE,
        capthick=CAPTHICK,
        color=color,
        label=label
    )
    for bar in bars: bar.set_alpha(0.5)
    for cap in caps: cap.set_alpha(0.5)

for mult in QMULTS:
    data = []
    for protocol in PROTOCOLS:
        for interrupt in INTERRUPTS:
            goodputs_total = []
            for run in RUNS:
                PATH = (
                    f"../../../paperExperiments/experiment7/csvs/"
                    f"{protocol}/{QMULTDICT[mult]}/{DELAY}ms/"
                    f"Disruption{interrupt}ms/run{run}/"
                )
                goodputPath = (
                    PATH + "singledumbbell.server[0].app[0]/goodput.csv"
                )
                if os.path.exists(goodputPath):
                    df = (pd.read_csv(goodputPath)
                          .reset_index(drop=True)
                          .loc[:, ['time','goodput']])
                    df['time'] = df['time'].astype(float).astype(int)
                    df = df.drop_duplicates('time').set_index('time')
                    goodputs_total.append(df['goodput'].values / 1e6)
                else:
                    print(f"Folder {PATH} not found.")

            if goodputs_total:
                all_pts = np.concatenate(goodputs_total, axis=0)
                data.append([
                    protocol, BW, DELAY, mult, interrupt,
                    all_pts.mean(), all_pts.std()
                ])

    summary = pd.DataFrame(
        data,
        columns=['protocol','goodput','delay','qmult','interrupt',
                 'goodput_total_mean','goodput_total_std']
    )

    fig, ax = plt.subplots(figsize=(4.5,1.2))
    for proto in PROTOCOLS:
        sub = (
            summary[summary['protocol']==proto]
            .set_index('interrupt')
        )
        plot_points(
            ax, sub,
            'goodput_total_mean', 'goodput_total_std',
            PROTOCOLS_MARKERS_LEO[proto],
            COLORS_LEO[proto],
            PROTOCOLS_FRIENDLY_NAME_LEO[proto]
        )

    ax.set(
        yscale='linear',
        xlabel='Interrupt time (ms)',
        ylabel='Goodput (Mb/s)'
    )
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_formatter(ScalarFormatter())

    markers = [PROTOCOLS_MARKERS_LEO[p] for p in PROTOCOLS]
    colors  = [COLORS_LEO[p] for p in PROTOCOLS]
    legend_labels = [PROTOCOLS_FRIENDLY_NAME_LEO[p] for p in PROTOCOLS]
    proxy_lines = [
        Line2D([0], [0],
                marker=mk,
                color=col,
                linestyle='-',
                linewidth=LINEWIDTH,
                markersize=6)
                for mk, col in zip(markers, colors)
    ]
    ax.legend(
        handles=proxy_lines,
        labels=legend_labels,
        ncol=4,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.2),
        frameon=False,
        columnspacing=1,
        handletextpad=0.5,
        labelspacing=0.1,
        borderaxespad=0.0,
        fontsize='x-small'
    )
    
    # after all your plotting calls…

    # and save with bbox_inches='tight' just to be sure
    fig.tight_layout()
    plt.subplots_adjust(top=1.3)
    plt.savefig(f"Avg_goodput_{mult}.pdf", dpi=1080)
    plt.close()