import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib.lines import Line2D

# existing style & constants
import scienceplots
plt.style.use('science')
plt.rcParams['text.usetex'] = True
plt.rcParams['axes.labelsize'] = "medium"
plt.rcParams['xtick.labelsize'] = "medium"
plt.rcParams['ytick.labelsize'] = "medium"

BW = 100
DELAY = 50
INTERRUPTS = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
QMULTS = [0.2, 1, 4]
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
PROTOCOLS = ['cubic', 'bbr', 'bbr3', 'orbtcp']
PROT_MARK = {'cubic': 'x', 'bbr': '.', 'orbtcp': '^', 'bbr3': '_'}
COLORS = {'cubic': '#0C5DA5', 'bbr': '#00B945', 'orbtcp': '#FF9500', 'bbr3': '#eb0909'}
NAMES = {'cubic': 'Cubic', 'bbr': 'BBRv1', 'orbtcp': 'LeoTCP', 'bbr3': 'BBRv3'}

LINEWIDTH = 0.30
ELINEWIDTH = 0.75
CAPSIZE = 2
CAPTHICK = ELINEWIDTH

# parameters for disruption spacing & post-disruption window
PERIOD_SEC = 5.0     # every 5 seconds a disruption occurs
WINDOW_SEC = (DELAY/1000)*50     # we only look 1 second after each disruption

def plot_points(ax, df, mean_col, std_col, mkr, col, label):
    if df.empty:
        return
    x = df.index
    y = df[mean_col]
    yerr = df[std_col]
    mk, caps, bars = ax.errorbar(
        x, y, yerr=yerr,
        marker=mkr,
        linestyle='-',
        linewidth=LINEWIDTH,
        elinewidth=ELINEWIDTH,
        capsize=CAPSIZE,
        capthick=CAPTHICK,
        color=col,
        label=label
    )
    for bar in bars:
        bar.set_alpha(0.5)
    for cap in caps:
        cap.set_alpha(0.5)

for qmult in QMULTS:
    records = []
    for proto in PROTOCOLS:
        for intr_ms in INTERRUPTS:
            samples = []
            intr_s = intr_ms / 1000.0

            for run in [1, 2, 3, 4, 5]:
                base = (
                    f"../../../paperExperiments/experiment7/csvs/"
                    f"{proto}/{QMULTDICT[qmult]}/{DELAY}ms/"
                    f"Disruption{intr_ms}ms/run{run}/"
                )
                fpath = base + "singledumbbell.server[0].app[0]/goodput.csv"
                if not os.path.exists(fpath):
                    print(f"  ⚠️ missing: {fpath}")
                    continue

                df = pd.read_csv(fpath)
                # do not drop duplicates; keep all measurements
                df = df.set_index('time').astype(float)

                t_max = df.index.max()
                n_periods = int(np.floor(t_max / PERIOD_SEC))
                # assume disruptions start at PERIOD_SEC, 2*PERIOD_SEC, ..., then last at n_periods*PERIOD_SEC
                for i in range(1, n_periods + 1):
                    t_event = i * PERIOD_SEC
                    t_start = t_event + intr_s
                    t_end = t_start + WINDOW_SEC
                    seg = df.loc[t_start:t_end, 'goodput']
                    if not seg.empty:
                        # convert to Mb/s
                        samples.append(seg.values / 1e6)

            if samples:
                all_pts = np.concatenate(samples)
                records.append([
                    proto, BW, DELAY, qmult, intr_ms,
                    all_pts.mean(), all_pts.std()
                ])

    # build DataFrame of results
    summary = pd.DataFrame(
        records,
        columns=[
            'protocol', 'bw', 'delay', 'qmult', 'interrupt_ms',
            'mean_goodput', 'std_goodput'
        ]
    )
    summary = summary.set_index('interrupt_ms')

    # now plot
    fig, ax = plt.subplots(figsize=(4.5, 1.2))
    for proto in PROTOCOLS:
        sub = summary[summary['protocol'] == proto]
        plot_points(
            ax, sub,
            'mean_goodput', 'std_goodput',
            PROT_MARK[proto],
            COLORS[proto],
            NAMES[proto]
        )

    ax.set(
        xlabel='Disruption duration (ms)',
        ylabel='Avg Goodput (Mbps)',
        yscale='linear'
    )
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_major_formatter(ScalarFormatter())

    # custom legend
    legend_items = [
        Line2D([0], [0], marker=PROT_MARK[p], color=COLORS[p],
               linestyle='-', linewidth=LINEWIDTH, markersize=6)
        for p in PROTOCOLS
    ]
    ax.legend(
        legend_items,
        [NAMES[p] for p in PROTOCOLS],
        ncol=4, loc='upper center', bbox_to_anchor=(0.5, 1.25),
        frameon=False, fontsize='small'
    )

    fig.tight_layout()
    plt.subplots_adjust(top=1.3)
    outname = f"Avg_goodput_{qmult}.pdf"
    plt.savefig(outname, dpi=1080, bbox_inches='tight')
    plt.close()
    print(f"Saved {outname}")