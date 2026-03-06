#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

# Configuration (adjust ROOT_PATH if needed)
ROOT_PATH = "../.."
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

# If your directory names differ, adjust here
RTT_DIR_FOR_CLIENT = {
    'constantClient': '20ms',     # common layout
    'pathChangeClient': '20ms',   # common layout
}


def compute_dynamic_rtt(root_path, qmults, protocols, flows, runs, verbose=True):
    """
    Computes average RTT over a window of 100 base RTTs immediately after CHANGE1.
    Adds verbose debug prints to troubleshoot missing files / empty windows / bad parsing.
    """
    client_types = list(BASE_RTT.keys())
    dynamic_rtt = {prot: {client: [] for client in client_types} for prot in protocols}

    missing_files = 0
    found_files = 0
    total_masked_rows = 0
    read_errors = 0

    for mult in qmults:
        if mult not in QMULTDICT:
            print(f"[ERROR] qmult {mult} not in QMULTDICT keys: {list(QMULTDICT.keys())}")
            continue

        for prot in protocols:
            for run in runs:
                for dumbbell in (1, 2):
                    client_type = 'constantClient' if dumbbell == 1 else 'pathChangeClient'
                    window_end = CHANGE1 + WINDOW_LENGTHS[client_type]

                    rtt_dir = RTT_DIR_FOR_CLIENT.get(client_type, "20ms")

                    if verbose:
                        print(
                            f"\n=== prot={prot} run={run} client_type={client_type} "
                            f"rtt_dir={rtt_dir} CHANGE1={CHANGE1} window_end={window_end:.3f} ==="
                        )

                    for flow_id in range(1, flows + 1):
                        csv_path = (
                            f"{root_path}/paperExperiments/experiment3/csvs/"
                            f"{prot}/{QMULTDICT[mult]}/{rtt_dir}/"
                            f"run{run}/"
                            f"doubledumbbellpathchange.{client_type}[{flow_id-1}].tcp.conn/rtt.csv"
                        )

                        if verbose:
                            print(f"[PATH] {csv_path}")

                        if not os.path.exists(csv_path):
                            missing_files += 1
                            if verbose:
                                print(f"[MISSING] {csv_path}")
                            continue

                        found_files += 1

                        try:
                            df = pd.read_csv(csv_path, usecols=['time', 'rtt'])
                        except Exception as e:
                            read_errors += 1
                            print(f"[READ ERROR] {csv_path}: {e}")
                            continue

                        if df.empty:
                            if verbose:
                                print(f"[EMPTY DF] {csv_path}")
                            continue

                        # Coerce to numeric; drop rows where conversion fails
                        df['time'] = pd.to_numeric(df['time'], errors='coerce')
                        df['rtt'] = pd.to_numeric(df['rtt'], errors='coerce')

                        bad_time = int(df['time'].isna().sum())
                        bad_rtt = int(df['rtt'].isna().sum())
                        if verbose and (bad_time or bad_rtt):
                            print(f"[COERCE] bad_time={bad_time} bad_rtt={bad_rtt}")

                        df = df.dropna(subset=['time', 'rtt'])
                        if df.empty:
                            if verbose:
                                print(f"[ALL NaN AFTER DROP] {csv_path}")
                            continue

                        tmin, tmax = float(df['time'].min()), float(df['time'].max())
                        if verbose:
                            print(f"[TIME RANGE] min={tmin:.3f} max={tmax:.3f} rows={len(df)}")

                        # Filter for 100 base RTTs after CHANGE1
                        mask = (df['time'] >= CHANGE1) & (df['time'] < window_end)
                        masked_count = int(mask.sum())
                        total_masked_rows += masked_count

                        if verbose:
                            print(
                                f"[MASK] rows_in_window={masked_count} "
                                f"(CHANGE1={CHANGE1}, window_end={window_end:.3f})"
                            )

                        if masked_count == 0:
                            if verbose:
                                # Show a few rows nearest to CHANGE1 for debugging
                                idx = (df['time'] - CHANGE1).abs().nsmallest(5).index
                                nearest = df.loc[idx, ['time', 'rtt']].sort_values('time')
                                print("[NEAREST TIMES TO CHANGE1]")
                                print(nearest.to_string(index=False))
                            continue

                        # Append samples (rtt assumed to be seconds; if it's already ms in your CSVs, remove *1000 later)
                        dynamic_rtt[prot][client_type].extend(df.loc[mask, 'rtt'].tolist())

    print("\n========== SUMMARY ==========")
    print(f"Found files: {found_files}")
    print(f"Missing files: {missing_files}")
    print(f"Read errors: {read_errors}")
    print(f"Total rows matched by mask: {total_masked_rows}")

    print("\nProtocol, ClientType, AvgRTT_100BaseRTTsAfterChange_ms, N")
    for prot in protocols:
        for client in client_types:
            samples = dynamic_rtt[prot][client]
            mean_rtt_ms = (np.mean(samples) * 1000) if samples else float('nan')
            print(f"{prot}, {client}, {mean_rtt_ms:.3f}, {len(samples)}")


if __name__ == '__main__':
    compute_dynamic_rtt(ROOT_PATH, QMULTS, PROTOCOLS, FLOWS, RUNS, verbose=True)