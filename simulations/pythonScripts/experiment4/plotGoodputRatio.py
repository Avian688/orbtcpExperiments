import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.transforms import offset_copy
import scienceplots
plt.style.use('science')
import os, sys
from matplotlib.ticker import ScalarFormatter
import numpy as np

plt.rcParams['text.usetex'] = True
plt.rcParams['axes.labelsize'] = "medium"
plt.rcParams['xtick.labelsize'] = "medium"
plt.rcParams['ytick.labelsize'] = "medium"

PROTOCOLS = ['cubic', 'bbr', 'bbr3', 'orbtcp']
BWS = [100]
DELAYS = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
QMULTS = [0.2, 1, 4]
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
RUNS = [1, 2, 3, 4, 5]

LINEWIDTH = 0.30
ELINEWIDTH = 0.75
CAPTHICK = ELINEWIDTH
CAPSIZE = 2

def plot_points_rtt(ax, df, data, error, marker, label):
    if not df.empty:
        xvals = df.index
        yvals = df[data]
        yerr = df[error]
        markers, caps, bars = ax.errorbar(
            xvals, yvals,
            yerr=yerr,
            marker=marker,
            linewidth=LINEWIDTH,
            elinewidth=ELINEWIDTH,
            capsize=CAPSIZE,
            capthick=CAPTHICK,
            label=label
        )
        [bar.set_alpha(0.5) for bar in bars]
        [cap.set_alpha(0.5) for cap in caps]

for mult in QMULTS:
    data = []
    for protocol in PROTOCOLS:
        for bw in BWS:
            for delay in DELAYS:
                start_time = 1.5 * delay
                end_time = 2 * delay
                keep_last_seconds = int(0.25 * delay)

                goodput_ratios_20 = []
                goodput_ratios_total = []

                for run in RUNS:
                    PATH = '../../../paperExperiments/experiment4/csvs/' + protocol + '/' + QMULTDICT.get(mult) + '/' + str(delay) + 'ms/run' + str(run) + '/'
                    receiver1Path = PATH + 'singledumbbell.server[0].app[0]/goodput.csv'
                    receiver2Path = PATH + 'singledumbbell.server[1].app[0]/goodput.csv'
                    if os.path.exists(receiver1Path) and os.path.exists(receiver2Path):
                        r1 = pd.read_csv(receiver1Path).reset_index(drop=True)
                        r2 = pd.read_csv(receiver2Path).reset_index(drop=True)

                        r1['time'] = r1['time'].apply(lambda x: int(float(x)))
                        r2['time'] = r2['time'].apply(lambda x: int(float(x)))

                        r1 = r1[(r1['time'] > start_time) & (r1['time'] < end_time)]
                        r2 = r2[(r2['time'] > start_time) & (r2['time'] < end_time)]

                        r1 = r1.drop_duplicates('time')
                        r2 = r2.drop_duplicates('time')

                        last_r1 = r1[r1['time'] >= end_time - keep_last_seconds].reset_index(drop=True)
                        last_r2 = r2[r2['time'] >= end_time - keep_last_seconds].reset_index(drop=True)

                        r1 = r1.set_index('time')
                        r2 = r2.set_index('time')
                        last_r1 = last_r1.set_index('time')
                        last_r2 = last_r2.set_index('time')

                        total = r1.join(r2, how='inner', lsuffix='1', rsuffix='2')[['goodput1', 'goodput2']].dropna()
                        partial = last_r1.join(last_r2, how='inner', lsuffix='1', rsuffix='2')[['goodput1', 'goodput2']].dropna()

                        goodput_ratios_20.append(partial.min(axis=1) / partial.max(axis=1))
                        goodput_ratios_total.append(total.min(axis=1) / total.max(axis=1))
                    else:
                        print("Files %s or %s not found." % (receiver1Path, receiver2Path))

                if goodput_ratios_20 and goodput_ratios_total:
                    gp20 = np.concatenate(goodput_ratios_20, axis=0)
                    gptot = np.concatenate(goodput_ratios_total, axis=0)
                    if gp20.size and gptot.size:
                        data.append([
                            protocol, bw, delay, delay/10, mult,
                            gp20.mean(), gp20.std(),
                            gptot.mean(), gptot.std()
                        ])

    summary_data = pd.DataFrame(
        data,
        columns=[
            'protocol', 'goodput', 'delay', 'delay_ratio',
            'qmult', 'goodput_ratio_20_mean', 'goodput_ratio_20_std',
            'goodput_ratio_total_mean', 'goodput_ratio_total_std'
        ]
    )

    fig, ax = plt.subplots(figsize=(4.5,1.2))
    ax.set_ylim([0, 1.1])

    for proto, marker in [('cubic', 'x'), ('bbr', '.'), ('orbtcp', '^'), ('bbr3', '_')]:
        df = summary_data[summary_data['protocol'] == proto].set_index('delay')
        plot_points_rtt(
            ax, df,
            'goodput_ratio_total_mean',
            'goodput_ratio_total_std',
            marker, proto
        )
   
    ax.set(yscale='linear', xlabel='RTT (ms)', ylabel='Goodput Ratio')
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_formatter(ScalarFormatter())

    # Commented out the 2-row "pyramid" legend that showed protocol names at the top:
    handles, labels = ax.get_legend_handles_labels()
    line_handles = [h[0] if isinstance(h, tuple) else h for h in handles]
    legend_map = dict(zip(labels, line_handles))
    handles_top = [
        legend_map.get('cubic'),
        legend_map.get('bbr'),
        legend_map.get('bbr3'),
        legend_map.get('orbtcp')
    ]
    labels_top = ['Cubic', 'BBRv1', 'BBRv3', 'LeoTCP']
    legend_top = plt.legend(
        handles_top, labels_top,
        ncol=4,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.2),
        columnspacing=1.0,
        handletextpad=0.5,
        labelspacing=0.1,
        borderaxespad=0.0,
        fontsize='small'
    )
    plt.gca().add_artist(legend_top)

    plt.savefig(f"goodput_ratio_intra_rtt_{mult}.pdf", dpi=1080)