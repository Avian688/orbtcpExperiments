#!/usr/bin/env python3
import os, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
plt.style.use('science')
import matplotlib as mpl
mpl.rcParams['text.usetex'] = False
pd.set_option('display.max_rows', None)

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
})

from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

ROOT_PATH = "../../.."
AQM = "fifo"
BWS = [100]       # in Mbit/s
BANDWIDTH = 100
DELAYS = [20]     # base delays in ms; final stored as [20,40] in DF
QMULTS = [0.2,1,4]
QMULTDICT = {0.2 : "smallbuffer", 1 : "mediumbuffer", 4 : "largebuffer" }
PROTOCOLS = ['cubic','bbr','orbtcp', 'bbr3']
FLOWS = 2
RUNS = [1,2,3,4,5]
CHANGE1 = 100     # cross interval start time
CHANGE2 = 200     # cross interval start time
# --------------------------------------------------------------------
# Confidence Ellipse (from script 1)
# --------------------------------------------------------------------
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

# --------------------------------------------------------------------
# Jain's Fairness Index function
# --------------------------------------------------------------------
def calculate_jains_index(bandwidths):
    n = len(bandwidths)
    sum_bw = sum(bandwidths)
    sum_bw_sq = sum(bw**2 for bw in bandwidths)
    return (sum_bw**2) / (n * sum_bw_sq) if sum_bw_sq != 0 else 0

# --------------------------------------------------------------------
# data_to_dd_df:
#   Computes Jain's fairness index, total throughput, average retransmission,
#   and rejoin utilization.
#
#   Rejoin utilization is computed over the interval [200, 200+delay] seconds
#   using the average of the normalized values from interfaces r2a-eth1 and r2b-eth1.
#
#   Additionally, retransmissions are now also computed for the rejoin interval,
#   so that the utilization can be corrected (subtracted) similarly to the cross interval.
# --------------------------------------------------------------------
def data_to_dd_df(root_path, aqm, bws, delays, qmults, protocols,
                  flows, runs, change1):

    results = []
    start_time = 0
    end_time = 100
    for mult in qmults:
        for bw in bws:
            for delay in delays:
                cross_start = change1
                cross_end = change1 + (delay/1000)*500  # cross interval duration remains 50 seconds
                for protocol in protocols:
                    BDP_IN_BYTES = int(bw * (2 ** 20) * 2 * delay * (10 ** -3) / 8)
                    BDP_IN_PKTS = BDP_IN_BYTES / 1500
                    cross_jains_list = []
                    goodput_list = []
                    util_list = []
                    rejoin_util_list = []  # List for rejoin utilization averages

                    for run in runs:
                        # Define the rejoin interval for retransmission calculations
                        #rejoin_start = 200
                        #rejoin_end = 200 + (delay/1000)*500
                        # This list will hold rejoin retransmission values for each dumbbell/flow
                        #rejoin_retr_values = []

                        receivers_goodput = { i: pd.DataFrame() for i in range(1, flows*2+1) }
                        #retr_values = []
                        # For each dumbbell and flow, read goodput and retransmission files
                        for dumbbell in range(1, 3):
                            for flow_id in range(1, flows+1):
                                #DELAY + 10 (one way so should be 20 but in ms) DELAY = delay/1000)*500
                                cross_start = CHANGE1
                                cross_end = CHANGE1 + int(((delay/1000)*500 if dumbbell == 1 else 25) / 5)
                                rejoin_start = CHANGE2
                                rejoin_end = CHANGE2 + int(((delay/1000)*500 if dumbbell == 1 else 25) / 5)

                                modName = "constantServer"
                                if(dumbbell == 2):
                                    modName = "pathChangeServer"
                                        
                                real_flow_id = flow_id + flows*(dumbbell-1)
                                # Read goodput CSV
                                csv_path = root_path + "/paperExperiments/experiment3/csvs/" + protocol + "/" + QMULTDICT.get(mult) + '/' + str(delay) + 'ms/run' + str(run) + '/doubledumbbellpathchange.' + modName + '[' + str(flow_id-1) + '].app[0]/goodput.csv'
                                
                                if os.path.exists(csv_path):
                                    df_csv = pd.read_csv(csv_path, usecols=['time','goodput'])
                                    df_csv['time'] = df_csv['time'].astype(float).astype(int)
                                    df_csv = df_csv.drop_duplicates('time').set_index('time')
                                    receivers_goodput[real_flow_id] = df_csv
                                else:
                                    print(f"File {csv_path} not found")
                                
                                # Read retransmission sysstat file (for both cross and rejoin intervals)
                                #sysstat_path = (f"{root_path}/{aqm}/DoubleDumbell_{bw}mbit_{delay}ms_"
                                #                f"{int(mult * BDP_IN_PKTS)}pkts_0loss_{flows}flows_22tcpbuf_"
                                #                f"{protocol}/run{run}/sysstat/etcp_c{dumbbell}_{flow_id}.log")
                                #if os.path.exists(sysstat_path):
                                #    systat = pd.read_csv(sysstat_path, sep=';').rename(columns={"# hostname": "hostname"})
                                #    retr_df = systat[['timestamp','retrans/s']]
                                #    start_timestamp = retr_df['timestamp'].iloc[0]
                                #    retr_df.loc[:, 'timestamp'] = retr_df['timestamp'] - start_timestamp + 1
                                #    retr_df = retr_df.rename(columns={'timestamp':'time'})
                                #    retr_df['time'] = retr_df['time'].astype(float).astype(int)
                                #    # Compute for cross interval
                                #    cross_df = retr_df[(retr_df['time'] >= cross_start) & (retr_df['time'] < cross_end)]
                                #    cross_df = cross_df.drop_duplicates('time').set_index('time')
                                #    retr_val = (cross_df * 1500 * 8 / (1024 * 1024)).mean().values[0]
                                #    retr_values.append(retr_val)
                                #    # Compute for rejoin interval
                                #    rejoin_df = retr_df[(retr_df['time'] >= rejoin_start) & (retr_df['time'] < rejoin_end)]
                                #    rejoin_df = rejoin_df.drop_duplicates('time').set_index('time')
                                #    retr_rejoin_val = (rejoin_df * 1500 * 8 / (1024 * 1024)).mean().values[0]
                                #    rejoin_retr_values.append(retr_rejoin_val)
                                #else:


                        
                        modules = ["constantServer[0]", "constantServer[1]", "pathChangeServer[0]", "pathChangeServer[1]"]
                        
                        dfs = []
                        for mod in modules:
                            modPath = root_path + "/paperExperiments/experiment3/csvs/" + protocol + "/" + QMULTDICT.get(mult) + '/' + str(delay) + 'ms/run' + str(run) + '/doubledumbbellpathchange.' + mod + '.app[0]/goodput.csv'
                            if os.path.exists(modPath):
                                    df_mod = pd.read_csv(modPath, usecols=['time','goodput'])
                                    df_mod['time'] = df_mod['time'].astype(float).astype(int)
                                    df_mod = df_mod.drop_duplicates('time').set_index('time')
                                    dfs.append(df_mod)
                            else:
                                print(f"File {modPath} not found")
                        
                        if dfs:
                            # Find the union of all time points
                            all_times = sorted(set().union(*[df.index for df in dfs]))

                            #Reindex each df to match the full time range and forward-fill missing values
                            dfs_filled = [df.reindex(all_times).ffill() for df in dfs]

                            # Sum all throughput values across dataframes
                            df_modAll = sum(dfs_filled)
                            df_modAll = df_modAll.loc[(df_modAll.index > cross_start) & (df_modAll.index <= cross_end)]
                            util_list.append(df_modAll.mean()/1000000)

                        else:
                            print("No valid data found.")
                            util_list.append(0)

                        dumb1Modules = ["constantServer[0]", "constantServer[1]"]
                        dumb2Modules = ["pathChangeServer[0]", "pathChangeServer[1]"]

                        dumb1Dfs = []
                        dumb2Dfs = []

                        for dum1Mod in dumb1Modules:
                            dum1ModPath = root_path + "/paperExperiments/experiment3/csvs/" + protocol + "/" + QMULTDICT.get(mult) + '/' + str(delay) + 'ms/run' + str(run) + '/doubledumbbellpathchange.' + dum1Mod + '.app[0]/goodput.csv'
                            if os.path.exists(dum1ModPath):
                                    df_dum1Mod = pd.read_csv(dum1ModPath, usecols=['time','goodput'])
                                    df_dum1Mod['time'] = df_dum1Mod['time'].astype(float).astype(int)
                                    df_dum1Mod = df_dum1Mod.drop_duplicates('time').set_index('time')
                                    dumb1Dfs.append(df_dum1Mod)
                            else:
                                print(f"File {dum1ModPath} not found")

                        for dum2Mod in dumb2Modules:
                            dum2ModPath = root_path + "/paperExperiments/experiment3/csvs/" + protocol + "/" + QMULTDICT.get(mult) + '/' + str(delay) + 'ms/run' + str(run) + '/doubledumbbellpathchange.' + mod + '.app[0]/goodput.csv'
                            if os.path.exists(dum2ModPath):
                                    df_dum2Mod = pd.read_csv(dum2ModPath, usecols=['time','goodput'])
                                    df_dum2Mod['time'] = df_dum2Mod['time'].astype(float).astype(int)
                                    df_dum2Mod = df_dum2Mod.drop_duplicates('time').set_index('time')
                                    dumb2Dfs.append(df_dum2Mod)
                            else:
                                print(f"File {dum2ModPath} not found")

                        if dumb1Dfs and dumb2Dfs:
                            # Find the union of all time points
                            all_timesDum1 = sorted(set().union(*[df.index for df in dumb1Dfs]))
                            all_timesDum2 = sorted(set().union(*[df.index for df in dumb2Dfs]))

                            #Reindex each df to match the full time range and forward-fill missing values
                            dfs_filledDum1 = [df.reindex(all_timesDum1).ffill() for df in dumb1Dfs]
                            dfs_filledDum2 = [df.reindex(all_timesDum2).ffill() for df in dumb2Dfs]

                            # Sum all throughput values across dataframes
                            df_modAllDum1 = sum(dfs_filledDum1)
                            df_modAllDum2 = sum(dfs_filledDum2)

                            df_modAllDum1 = df_modAllDum1.loc[(df_modAllDum1.index > rejoin_start) & (df_modAllDum1.index <= rejoin_end)]
                            df_modAllDum2 = df_modAllDum2.loc[(df_modAllDum2.index > rejoin_start) & (df_modAllDum2.index <= rejoin_end)]

                            avg_rejoin_util = (df_modAllDum1.mean() + df_modAllDum2.mean())/2
                            rejoin_util_list.append(avg_rejoin_util/1000000)
                        else:
                            print("No valid data found.")
                        

                    

                        # Compute Jain's fairness for this run using the goodput data
                        cross_averages = []
                        for f_id in range(1, flows*2+1):
                            df_flow = receivers_goodput[f_id]
                            if df_flow.empty:
                                cross_averages.append(0)
                            else:
                                cross_slice = df_flow[(df_flow.index >= cross_start) & (df_flow.index < cross_start+(delay/1000)*500)]
                                cross_averages.append(cross_slice['goodput'].mean() if not cross_slice.empty else 0)
                        cross_jain = calculate_jains_index(cross_averages)
                        cross_jains_list.append(cross_jain)
                        run_goodput = np.sum(cross_averages)
                        goodput_list.append(run_goodput)
                        # Compute average rejoin retransmission for this run
                    # End runs loop

                    cross_mean = np.mean(cross_jains_list) if cross_jains_list else 0
                    cross_std  = np.std(cross_jains_list) if cross_jains_list else 0
                    goodput_mean = np.mean(goodput_list) if goodput_list else 0
                    goodput_std  = np.std(goodput_list) if goodput_list else 0
                    util_mean = np.mean(util_list) if util_list else 0
                    util_std  = np.std(util_list) if util_list else 0
                    rejoin_util_mean = np.mean(rejoin_util_list) if rejoin_util_list else 0
                    rejoin_util_std  = np.std(rejoin_util_list) if rejoin_util_list else 0

                    results.append([
                        protocol, bw, delay, mult,
                        cross_mean, cross_std,
                        goodput_mean, goodput_std,
                        util_mean, util_std,
                        rejoin_util_mean, rejoin_util_std,
                        np.asarray(cross_jains_list, dtype=np.float32), 
                        np.asarray(util_list, dtype=np.float32),
                        np.asarray(rejoin_util_list, dtype=np.float32),
                    
                    ])

                    

    columns = [
        'protocol','bandwidth','min_delay','qmult',
        'fairness_cross_mean','fairness_cross_std',
        'goodput_cross_mean','goodput_cross_std',
        'util_mean', 'util_std',
        'rejoin_util_mean', 'rejoin_util_std',
        'fairness_cross_list', 'util_list',
        'rejoin_util_list'

    ]
    return pd.DataFrame(results, columns=columns)


def plot_dd_scatter_jains_vs_util(df, delays=[10,20], qmults=[0.2,1,4]):
    MARK_COLOR_MAP = {
        'cubic':   '#0088ff',
        'bbr':    '#00ff5f',
        'orbtcp':    '#fd970c',
        'bbr3':    '#ff0a0a'
    }

    COLOR_MAP = {
        'cubic':   '#0C5DA5',
        'bbr':    '#00B945',
        'orbtcp':    '#FF9500',
        'bbr3':    '#eb0909'
    }

    REJOIN_COLOR_MAP = {
        'cubic':   '#07355e',
        'bbr':    '#024c1d',
        'orbtcp':    '#6d4102',
        'bbr3':    '#ab0303'
    }

    CROSS_MARKER   = '^'  # triangle for Cross
    REJOIN_MARKER  = '*'  # circle for Rejoin

    for q in qmults:
        fig, ax = plt.subplots(figsize=(3,1.9))  

        # 1) Plot data (unfilled markers, no legend labels)
        for prot in df['protocol'].unique():
            sub_df = df[(df['qmult'] == q) & (df['protocol'] == prot)]
            if sub_df.empty:
                continue

            x = sub_df['fairness_cross_mean'].values
            y_cross = sub_df['util_mean'].values / BANDWIDTH
            y_rejoin = sub_df['rejoin_util_mean'].values / BANDWIDTH

            # Cross (triangle)

            ellipseX =  sub_df['fairness_cross_list'].values[0]
            ellipseYCross =  sub_df['util_list'].values[0].flatten()/BANDWIDTH
            ellipseYRejoin =  sub_df['rejoin_util_list'].values[0].flatten()/BANDWIDTH

            confidence_ellipse(ellipseX, ellipseYRejoin, ax, facecolor=REJOIN_COLOR_MAP.get(prot, 'gray'), edgecolor='none', alpha=0.6)
            confidence_ellipse(ellipseX, ellipseYCross, ax, facecolor=COLOR_MAP.get(prot, 'gray'), edgecolor='none', alpha=0.6)

            ax.scatter(
                x, y_cross,
                marker=CROSS_MARKER, s=60,
                facecolors='none',
                edgecolors=MARK_COLOR_MAP.get(prot, 'gray'),
                alpha=1.0
            )
        
            # Rejoin (circle)
            ax.scatter(
                x, y_rejoin,
                marker=REJOIN_MARKER, s=60,
                facecolors='none',
                edgecolors=MARK_COLOR_MAP.get(prot, 'gray'),
                alpha=1.0
            )
            
            # confidence_ellipse(x, y_rejoin, ax, facecolor=COLOR_MAP.get(prot, 'gray'), edgecolor='none', alpha=0.25)
            # confidence_ellipse(x, y_cross_minus_retr, ax, facecolor=COLOR_MAP.get(prot, 'gray'), edgecolor='none', alpha=0.25)
            # confidence_ellipse(x, y_rejoin_minus_retr, ax, facecolor=COLOR_MAP.get(prot, 'gray'), edgecolor='none', alpha=0.25)

        # 2) TOP LEGEND (protocols only) - in figure coords so it’s truly above
        proto_handles = [Line2D([], [], color=COLOR_MAP[p], linewidth=1) for p in PROTOCOLS]
        proto_labels = PROTOCOLS
        # leg1 = fig.legend(
        #     proto_handles[:3], proto_labels[:3],
        #     loc='upper center',
        #     bbox_to_anchor=(0.5, 1.10),
        #     ncol=3, frameon=False,
        #     fontsize=7, columnspacing=1.0,
        #     handlelength=2.5, handletextpad=0.7
        # )
        # fig.add_artist(leg1)

        # leg2 = fig.legend(
        #     proto_handles[3:], proto_labels[3:],
        #     loc='upper center',
        #     bbox_to_anchor=(0.5, 1.),
        #     ncol=2, frameon=False,
        #     fontsize=7, columnspacing=1.0,
        #     handlelength=2.5, handletextpad=0.7
        # )

        # 3) IN-PLOT LEGEND: Cross vs Rejoin
        cross_handle = ax.scatter(
            [], [],
            marker=CROSS_MARKER, s=80,
            facecolors='none', edgecolors='black',
            label='Cross'
        )
        rejoin_handle = ax.scatter(
            [], [],
            marker=REJOIN_MARKER, s=80,
            facecolors='none', edgecolors='black',
            label='Rejoin'
        )
        shape_legend = ax.legend(
            [cross_handle, rejoin_handle],
            ['Cross', 'Rejoin'],
            fontsize=6,
            loc='upper left',
            markerscale=0.7
        )
        ax.add_artist(shape_legend)

        ax.set_xlabel("Jain's Fairness Index")
        ax.set_ylabel("Norm. Throughput")
        ax.set_xlim([0.5, 1.05])
        ax.set_ylim([0.4, 1.05])


        fig.tight_layout()
        plt.subplots_adjust(left=0.18, top=0.85)

        print("SAVING")
        plt.savefig(f"jains_vs_util_qmult_{q}.pdf", dpi=1080, bbox_inches='tight',  pad_inches=0.1)
        plt.close(fig)





if __name__ == "__main__":
    # 1) Load the data (with retransmission calculations and rejoin utilization)
    dd_df = data_to_dd_df(ROOT_PATH, AQM, BWS, DELAYS, QMULTS,
                          PROTOCOLS, FLOWS, RUNS, CHANGE1)
    dd_df.to_csv("dd_summary_data.csv", index=False)

    # 2) Plot: X = Jain's fairness, Y = normalized throughput (with secondary points subtracting retransmission,
    #    and additional rejoin utilization markers)
    plot_dd_scatter_jains_vs_util(dd_df, delays=DELAYS, qmults=QMULTS)
