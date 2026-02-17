#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

# Configuration (adjust ROOT_PATH if needed)
ROOT_PATH = "../../.."
QMULTS = [1]
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
PROTOCOLS = ['cubic', 'bbr', 'orbtcp', 'bbr3']
FLOWS = 2
RUNS = [1, 2, 3, 4, 5]
CHANGE1 = 101  # first change time in seconds
# Base RTTs in seconds for each client type
BASE_RTT = {'constantClient': 0.050, 'pathChangeClient': 0.020}
# Calculate window lengths: 100 base RTTs
WINDOW_LENGTHS = {client: 100 * rtt for client, rtt in BASE_RTT.items()}


def compute_dynamic_rtt(root_path, qmults, protocols, flows, runs):
    # Prepare structure: protocol -> client type -> list of RTT samples
    client_types = list(BASE_RTT.keys())
    dynamic_rtt = {prot: {client: [] for client in client_types} for prot in protocols}

    for mult in qmults:
        for prot in protocols:
            for run in runs:
                for dumbbell in (1, 2):
                    client_type = 'constantClient' if dumbbell == 1 else 'pathChangeClient'
                    window_end = CHANGE1 + WINDOW_LENGTHS[client_type]
                    for flow_id in range(1, flows + 1):
                        csv_path = (
                            f"{root_path}/paperExperiments/experiment3/csvs/"
                            f"{prot}/{QMULTDICT[mult]}/20ms/"
                            f"run{run}/"
                            f"doubledumbbellpathchange.{client_type}[{flow_id-1}].tcp.conn/rtt.csv"
                        )
                        print(csv_path)
                        if not os.path.exists(csv_path):
                            continue
                        df = pd.read_csv(csv_path, usecols=['time', 'rtt'])
                        df['time'] = df['time'].astype(float)

                        # Filter for 100 base RTTs after the first change
                        mask = (df['time'] >= CHANGE1) & (df['time'] < window_end)
                        if mask.any():
                            dynamic_rtt[prot][client_type].extend(df.loc[mask, 'rtt'].tolist())

    # Print results in milliseconds
    print("Protocol, ClientType, AvgRTT_100BaseRTTsAfterChange_ms")
    for prot in protocols:
        for client in client_types:
            samples = dynamic_rtt[prot][client]
            mean_rtt = np.mean(samples) * 1000 if samples else float('nan')
            print(f"{prot}, {client}, {mean_rtt:.3f}")


if __name__ == '__main__':
    compute_dynamic_rtt(ROOT_PATH, QMULTS, PROTOCOLS, FLOWS, RUNS)