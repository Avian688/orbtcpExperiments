import os
import numpy as np
import pandas as pd

# Constants
base_dir = "../../../paperExperiments/experimentInitNumFlows/csvs"
protocols = ["Orbtcp", "OrbtcpNoInitFlows"]
buffer = "mediumbuffer"
delay = "100ms"
num_clients = 65  # number of client connections
num_runs = 5      # number of runs per protocol

# Late-flow start times: 1 flow at 10s, 2 at 20s, 4 at 30s, 8 at 40s
late_starts = [10] + [20]*2 + [30]*4 + [40]*8
# Map client index → join time
late_start_dict = {50 + idx: start for idx, start in enumerate(late_starts)}

for protocol in protocols:
    all_rtts = []
    first100_rtts = []
    # Initialize container for late-flow RTT samples
    join_rtt_groups = {t: [] for t in set(late_starts)}

    for run in range(1, num_runs + 1):
        run_path = os.path.join(base_dir, protocol, buffer, delay, f"run{run}")
        for i in range(num_clients):
            fp = os.path.join(
                run_path,
                f"singledumbbell.client[{i}].tcp.conn",
                "rtt.csv",
            )
            if not os.path.exists(fp):
                continue

            # Read RTT and convert to ms
            df = pd.read_csv(fp)
            df["rtt_ms"] = df["rtt"].astype(float) * 1000
            rtts = df["rtt_ms"].tolist()

            # Aggregate overall and first-100 samples
            all_rtts.extend(rtts)
            first100_rtts.extend(rtts[:100])

            # If this is a late-flow, collect its first-100 post-join samples
            if i in late_start_dict:
                join_time = late_start_dict[i]
                join_rtt_groups[join_time].extend(rtts[:100])

    if not all_rtts:
        print(f"No RTT data found for {protocol}")
        continue

    # Compute and print averages
    avg_all = np.mean(all_rtts)
    avg_first100 = np.mean(first100_rtts)
    print(f"{protocol}: Average RTT over first 100 samples = {avg_first100:.2f} ms")
    print(f"{protocol}: Average RTT over all samples = {avg_all:.2f} ms")

    # Print average RTT per join-time group
    for join_time in sorted(join_rtt_groups):
        samples = join_rtt_groups[join_time]
        if samples:
            avg = np.mean(samples)
            print(
                f"{protocol}: Average RTT of flows joining at {join_time}s over first 100 samples = {avg:.2f} ms"
            )
