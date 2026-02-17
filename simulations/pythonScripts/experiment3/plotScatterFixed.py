#!/usr/bin/env python3
import os, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
plt.style.use('science')
import matplotlib as mpl
mpl.rcParams['text.usetex'] = True
pd.set_option('display.max_rows', None)
plt.rcParams['axes.labelsize'] = "medium"
plt.rcParams['xtick.labelsize'] = "medium"
plt.rcParams['ytick.labelsize'] = "medium"

from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

ROOT_PATH = "../../.."
AQM = "fifo"
BWS = [100]       # in Mbit/s
BANDWIDTH = 100
DELAYS = [10]     # base delays in ms; final stored as [20,40] in DF
QMULTS = [0.2,1,4]
QMULTDICT = {0.2 : "smallbuffer", 1 : "mediumbuffer", 4 : "largebuffer" }
PROTOCOLS = ['cubic','bbr','orbtcp', 'bbr3']
FLOWS = 2
RUNS = [1,2,3,4,5]
CHANGE1 = 101    # cross interval start time
CHANGE2 = 201   # cross interval start time
COLORS_LEO           = {'cubic':'#0C5DA5','bbr':'#00B945','orbtcp':'#FF9500','bbr3':'#eb0909'}

def confidence_ellipse(x, y, ax, n_std=1.0, facecolor='none', **kwargs):
    if x.size != y.size:
        raise ValueError("x and y must be the same size")
    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0),
                      width=ell_radius_x * 2,
                      height=ell_radius_y * 2,
                      facecolor=facecolor,
                      **kwargs)
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)
    transf = (transforms.Affine2D()
              .rotate_deg(45)
              .scale(scale_x, scale_y)
              .translate(mean_x, mean_y))
    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)

def calculate_jains_index(bandwidths):
    """
    Calculate Jain's fairness index for a list of bandwidth values.
    """
    n = len(bandwidths)
    sum_bw = sum(bandwidths)
    sum_bw_sq = sum(bw**2 for bw in bandwidths)
    return (sum_bw**2) / (n * sum_bw_sq) if sum_bw_sq != 0 else 0


def data_to_dd_df(root_path, aqm, bws, delays, qmults, protocols,
                  flows, runs):

    results = []
    for mult in qmults:
        for bw in bws:
            for delay in delays:
                for protocol in protocols:
                    BDP_IN_BYTES = int(bw * (2 ** 20) * 2 * delay * (10 ** -3) / 8)
                    BDP_IN_PKTS = BDP_IN_BYTES / 1500

                    cross_jains_list = []
                    rejoin_jains_list = []
                    goodput_list = []
                    retr_list = []
                    util_list = []
                    rejoin_util_list = []
                    rejoin_retr_list = []
                    sum_cross = []
                    sum_rejoin = []

                    for run in runs:
                        retr_values = []
                        rejoin_retr_values = []
                        receivers_goodput = {i: pd.DataFrame() for i in range(1, flows*2+1)}

                        # Load per‐receiver csv and sysstat data
                        for dumbbell in range(1, 3):
                            for flow_id in range(1, flows+1):
                                real_flow_id = flow_id + flows*(dumbbell-1)
                                modName = "constantServer"
                                if(dumbbell == 2):
                                    modName = "pathChangeServer"
                                csv_path = root_path + "/paperExperiments/experiment3/csvs/" + protocol + "/" + QMULTDICT.get(mult) + '/' + str(delay*2) + 'ms/run' + str(run) + '/doubledumbbellpathchange.' + modName + '[' + str(flow_id-1) + '].app[0]/goodput.csv'
                                
                                if os.path.exists(csv_path):
                                    df_csv = pd.read_csv(csv_path, usecols=['time','goodput'])
                                    df_csv = df_csv.assign(goodput=df_csv['goodput'] / 1000000)
                                    df_csv['time'] = df_csv['time'].astype(float).astype(int)
                                    df_csv = df_csv.drop_duplicates('time').set_index('time')
                                    receivers_goodput[real_flow_id] = df_csv
                                else:
                                    print(f"File {csv_path} not found")

                                retr_values.append(0)
                                rejoin_retr_values.append(0)

                        cross_averages = []
                        offset = 0
                        for f_id in range(1, flows*2+1):
                            df_flow = receivers_goodput[f_id]
                            if df_flow.empty:
                                cross_averages.append(0)
                            else:
                                cs = CHANGE1 + offset
                                ce = CHANGE1 + 5 + offset
                                sl = df_flow.loc[cs:ce, 'goodput']
                                cross_averages.append(sl.mean() if not sl.empty else 0)

                        rejoin_averages_d1 = []
                        rejoin_averages_d2 = []
                        offset = 0
                        for f_id in range(1, 3):
                            df_flow_d1 = receivers_goodput[f_id]#
                            df_flow_d2 = receivers_goodput[f_id+2]#
                            if df_flow.empty:
                                cross_averages.append(0)
                            else:
                                cs = CHANGE1 + offset
                                ce = CHANGE1 + int((delay if f_id<=flows else 25)/5) + offset
                                sl = df_flow_d1.loc[cs:ce, 'goodput']
                                s2 = df_flow_d2.loc[cs:ce, 'goodput']
                                rejoin_averages_d1.append(sl.mean() if not sl.empty else 0)
                                rejoin_averages_d2.append(s2.mean() if not s2.empty else 0)

                        offset = 0
                        bw_cross = pd.concat(
                            [receivers_goodput[f].loc[CHANGE1:CHANGE1+int((delay)/5), 'goodput']
                             for f in range(1, flows*2+1)], axis=1
                        ).fillna(0).sum(axis=1)

                        bw_rejoin1 = pd.concat(
                            [receivers_goodput[f].loc[CHANGE2+offset:CHANGE2+5+offset, 'goodput']
                             for f in range(1, 3)], axis=1
                        ).fillna(0).sum(axis=1)



                        bw_rejoin2 = pd.concat(
                            [receivers_goodput[f].loc[CHANGE2+offset:CHANGE2+2+offset, 'goodput']
                             for f in range(3, 5)], axis=1
                        ).fillna(0).sum(axis=1)
                        sum_cross.append(bw_cross.mean())
                        sum_rejoin.append((bw_rejoin1.mean() + bw_rejoin2.mean())/2)


                        cross_jains_list.append(calculate_jains_index(cross_averages))

                        rejoin_jains_list.append((calculate_jains_index(rejoin_averages_d1) + calculate_jains_index(rejoin_averages_d2))/2)
                        print(rejoin_jains_list)
                        goodput_list.append(sum(cross_averages))
                        retr_list.append(np.mean(retr_values))
                        rejoin_retr_list.append(np.mean(rejoin_retr_values))
                    
                    print(sum_cross)
                    # After runs
                    results.append([
                        protocol, bw, delay*2, mult,
                        np.mean(cross_jains_list), np.std(cross_jains_list),
                        np.mean(rejoin_jains_list), np.std(rejoin_jains_list),
                        np.mean(goodput_list), np.std(goodput_list),
                        np.mean(retr_list), np.std(retr_list),
                        np.mean(sum_cross), np.std(sum_cross),
                        np.mean(sum_rejoin), np.std(sum_rejoin),
                        np.mean(util_list), np.std(util_list),
                        np.mean(rejoin_util_list), np.std(rejoin_util_list),
                        np.mean(rejoin_retr_list), np.std(rejoin_retr_list),
                        np.asarray(cross_jains_list,      dtype=np.float32),
                        np.asarray(rejoin_jains_list,     dtype=np.float32),
                        np.asarray(util_list,             dtype=np.float32),
                        np.asarray(rejoin_util_list,      dtype=np.float32),
                        np.asarray(retr_list,             dtype=np.float32),
                        np.asarray(rejoin_retr_list,      dtype=np.float32),
                        np.asarray(sum_cross,             dtype=np.float32),
                        np.asarray(sum_rejoin,            dtype=np.float32)
                    ])

    columns = [
        'protocol','bandwidth','min_delay','qmult',
        'fairness_cross_mean','fairness_cross_std',
        'fairness_rejoin_mean','fairness_rejoin_std',
        'goodput_cross_mean','goodput_cross_std',
        'retr_cross_mean','retr_cross_std',
        'goodput_aggregated_cross_mean','goodput_aggregated_cross_std',
        'goodput_aggregated_rejoin_mean','goodput_aggregated_rejoin_std',
        'util_mean','util_std',
        'rejoin_util_mean','rejoin_util_std',
        'retr_rejoin_mean','retr_rejoin_std',
        'fairness_cross_list', 'fairness_rejoin_list',
        'util_list',
        'rejoin_util_list','retr_list',
        'rejoin_retr_list',
        'aggregated_cross_list',
        'aggregated_rejoin_list'
    ]
    return pd.DataFrame(results, columns=columns)


def plot_dd_scatter_jains_vs_util(df, delays=[10,20], qmults=[0.2,1,4]):
    CROSS_MARKER  = '^'
    REJOIN_MARKER = '*'

    for q in qmults:
        fig, ax = plt.subplots(figsize=(4.5,1.2))
        for prot in df['protocol'].unique():
            sub_df = df[(df['qmult']==q) & (df['protocol']==prot)]
            if sub_df.empty:
                continue

            # per-run arrays for ellipse
            x_cross = sub_df['fairness_cross_list'].values[0]
            x_rejoin = sub_df['fairness_rejoin_list'].values[0]
            y_cross  = sub_df['aggregated_cross_list'].values[0] / 100
            y_rejoin = sub_df['aggregated_rejoin_list'].values[0] / 100

            # draw filled ellipses
            confidence_ellipse(x_cross, y_cross,  ax, facecolor=COLORS_LEO.get(prot,'gray'), alpha=0.6)
            confidence_ellipse(x_rejoin, y_rejoin, ax, facecolor=COLORS_LEO.get(prot,'gray'), alpha=0.6)

            print(sub_df['goodput_aggregated_cross_mean']/100)
            # scatter mean points
            ax.scatter(
                sub_df['fairness_cross_mean'],
                sub_df['goodput_aggregated_cross_mean']/100,
                marker=CROSS_MARKER, s=60,
                facecolors='none', edgecolors=COLORS_LEO.get(prot,'gray')
            )
            ax.scatter(
                sub_df['fairness_rejoin_mean'],
                sub_df['goodput_aggregated_rejoin_mean']/100,
                marker=REJOIN_MARKER, s=60,
                facecolors='none', edgecolors=COLORS_LEO.get(prot,'gray')
            )



        # marker legend (Change 1 & Change 2)
        ch = ax.scatter([], [], marker=CROSS_MARKER, s=80,
                        facecolors='none', edgecolors='black', label='Change 1')
        rh = ax.scatter([], [], marker=REJOIN_MARKER, s=80,
                        facecolors='none', edgecolors='black', label='Change 2')
        marker_legend = ax.legend(handles=[ch, rh], loc='upper left',
                                  fontsize="medium", markerscale=0.7)
        ax.add_artist(marker_legend)

        # protocol legend (colored lines)
        proxy_lines = [
            Line2D([0], [0], color=COLORS_LEO[p], lw=1)
            for p in ['cubic', 'bbr', 'bbr3', 'orbtcp']
        ]
        proto_labels = ['Cubic', 'BBRv1', 'BBRv3', 'LeoTCP']
        proto_legend = ax.legend(proxy_lines, proto_labels,
                                 ncol=4, loc='upper center',
                                 bbox_to_anchor=(0.5, 1.2),
                                 fontsize='small', columnspacing=1.0,
                                 handletextpad=0.5, borderaxespad=0.0)
        ax.add_artist(proto_legend)

        ax.set_xlabel("Jain's Fairness Index")
        ax.set_ylabel("Norm. Goodput", fontsize="medium")
        ax.set_xlim(0.4, 1.05)
        ax.set_ylim(0.4, 1.05)

        plt.savefig(f"jains_vs_goodput_qmult_{q}.pdf",
                    dpi=1080, bbox_inches='tight')
        plt.close(fig)


if __name__ == "__main__":
    dd_df = data_to_dd_df(ROOT_PATH, AQM, BWS, DELAYS, QMULTS, PROTOCOLS, FLOWS, RUNS)
    plot_dd_scatter_jains_vs_util(dd_df, delays=DELAYS, qmults=QMULTS)