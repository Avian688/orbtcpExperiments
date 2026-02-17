#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

# ─── Experiment Setup ─────────────────────────────────────────────────────────
# Analyze Pair1 and Pair3 (but label Pair3 as “Pair2” in the outputs)
pairs2      = ['Pair1', 'Pair3']
pair_labels = {'Pair1': 'Pair1', 'Pair3': 'Pair2'}

protocols   = ['cubic', 'bbr', 'bbr3', 'orbtcp']  # LeoTCP last
RUNS        = [1, 2, 3, 4, 5]

# Friendly names for printing
FRIENDLY    = {'cubic':'Cubic', 'bbr':'BBRv1', 'bbr3':'BBRv3', 'orbtcp':'LeoTCP'}

# ─── RTT Computation ──────────────────────────────────────────────────────────
def avg_rtt(proto, pair):
    """
    For a given protocol and pair, iterate over all RUNS and both client instances (srv=0,1),
    load the RTT CSVs under leoconstellation.client[{srv}].tcp.conn,
    and return the overall mean RTT (in whatever unit the CSV uses, e.g. ms).
    """
    base = os.path.join("../../../paperExperiments/experiment10/csvs",
                        proto.title(), pair)
    rtts = []
    for run in RUNS:
        for srv in [0, 1]:
            # path to the TCP connection metrics directory
            conn_dir = os.path.join(base,
                                    f"run{run}",
                                    f"leoconstellation.client[{srv}].tcp.conn")
            # assume the file is named "rtt.csv"
            fpath = os.path.join(conn_dir, "rtt.csv")
            if not os.path.exists(fpath):
                continue
            df = pd.read_csv(fpath)
            if 'rtt' in df.columns:
                # mean RTT for this run & srv
                rtts.append(df['rtt'].mean())
    return float(np.mean(rtts)) if rtts else float('nan')

# ─── Main: print out averages ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nAverage RTT for all runs (per protocol, per pair):\n")
    for proto in protocols:
        print(f"{FRIENDLY[proto]}:")
        for p in pairs2:
            mean_rtt = avg_rtt(proto, p)
            if np.isnan(mean_rtt):
                print(f"  {pair_labels[p]}: no data found")
            else:
                print(f"  {pair_labels[p]}: {mean_rtt:.2f} ms")