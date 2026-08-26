import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np
import pandas as pd
import scienceplots

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plotDataExport import export_heatmap
from plotProtocolSupport import (
    HEATMAP_PROTOCOL_TICK_STYLE,
    LEO_PROTOCOLS,
    PROTOCOL_LABELS,
)
from raynetExperimentSupport import protocol_config_prefix

plt.style.use("science")
plt.rcParams["font.size"] = 40
plt.rcParams["text.usetex"] = True

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_ROOT = (SCRIPT_DIR / "../../paperExperiments/experiment9/csvs").resolve()

protocols = LEO_PROTOCOLS
RUNS = [1, 2, 3, 4, 5]
QMULTS = [1]
QMULTDICT = {0.2: "smallbuffer", 1: "mediumbuffer", 4: "largebuffer"}
SOURCE_TERMINALS = [0, 1]
SIMULATION_END_SECONDS = 300.0
SAMPLE_INTERVAL_SECONDS = 1.0
BITS_PER_MEGABIT = 1_000_000.0

paths_info = {
    "SeattleNewYork_isl": {"label": "SEA to NY (ISL)"},
    "SeattleNewYork_bentpipe": {"label": "SEA to NY (BP)"},
    "SanDiegoNewYork_isl": {"label": "SD to NY (ISL)"},
    "SanDiegoNewYork_bentpipe": {"label": "SD to NY (BP)"},
    "NewYorkLondon_isl": {"label": "NY to LDN (ISL)"},
    "SanDiegoShanghai_isl": {"label": "SD to SHA (ISL)"},
}

path_keys = list(paths_info)
row_labels = [paths_info[key]["label"] for key in path_keys]


def average_rate_mbps(filepath):
    frame = pd.read_csv(filepath)
    if not {"time", "retransmissionRate"}.issubset(frame.columns):
        return None

    samples = frame[["time", "retransmissionRate"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna().sort_values("time")
    if samples.empty:
        return None

    first_sample_time = float(samples["time"].iloc[0])
    final_slot = int(
        np.floor(
            (SIMULATION_END_SECONDS - first_sample_time)
            / SAMPLE_INTERVAL_SECONDS
        )
    )
    if final_slot < 0:
        return None

    sample_slots = np.rint(
        (samples["time"] - first_sample_time) / SAMPLE_INTERVAL_SECONDS
    ).astype(int)
    rates_bps = pd.Series(
        samples["retransmissionRate"].to_numpy(dtype=float),
        index=sample_slots,
    ).groupby(level=0).last()
    rates_bps = rates_bps[(rates_bps.index >= 0) & (rates_bps.index <= final_slot)]
    if rates_bps.empty:
        return None

    # removeRepeats stores only rate changes, so restore the one-second samples.
    rates_bps = rates_bps.reindex(range(final_slot + 1)).ffill().bfill()
    return float(rates_bps.mean() / BITS_PER_MEGABIT)


def compute_mean_std(path_key, protocol, queue_multiplier):
    source_destination, mode = path_key.split("_", 1)
    run_root = (
        CSV_ROOT
        / protocol_config_prefix(protocol)
        / source_destination
        / mode
        / QMULTDICT[queue_multiplier]
    )

    run_means = []
    for run in RUNS:
        flow_means = []
        for terminal in SOURCE_TERMINALS:
            rate_file = (
                run_root
                / f"run{run}"
                / f"leoconstellation.userTerminal[{terminal}].tcp.conn"
                / "retransmissionRate.csv"
            )
            if not rate_file.exists():
                print(f"Missing retransmission rate file: {rate_file}")
                break

            rate_mbps = average_rate_mbps(rate_file)
            if rate_mbps is None:
                print(f"Invalid retransmission rate file: {rate_file}")
                break
            flow_means.append(rate_mbps)

        if len(flow_means) == len(SOURCE_TERMINALS):
            run_means.append(float(np.mean(flow_means)))

    if not run_means:
        return np.nan, np.nan
    return float(np.mean(run_means)), float(np.std(run_means))


df_mean = {}
df_std = {}
for queue_multiplier in QMULTS:
    mean_df = pd.DataFrame(index=row_labels, columns=protocols, dtype=float)
    std_df = pd.DataFrame(index=row_labels, columns=protocols, dtype=float)
    for path_key, row_label in zip(path_keys, row_labels):
        for protocol in protocols:
            mean, std = compute_mean_std(path_key, protocol, queue_multiplier)
            mean_df.at[row_label, protocol] = mean
            std_df.at[row_label, protocol] = std
    df_mean[queue_multiplier] = mean_df
    df_std[queue_multiplier] = std_df

    export_heatmap(
        f"heatmap_retransmission_rate_q{queue_multiplier}_points.csv",
        mean_df,
        std_df,
        metadata={
            "experiment": "experiment9",
            "plot": "heatmap_retransmission_rate",
            "qmult": queue_multiplier,
            "unit": "Mbps",
            "aggregation": (
                "Mean of the two source-flow retransmission rates within each "
                "run, then mean and standard deviation across five runs."
            ),
            "description": (
                "Final heatmap cells for average retransmission rate and "
                "across-run standard deviation."
            ),
        },
    )

cmap = LinearSegmentedColormap.from_list(
    "g_y_r", ["green", "yellow", "red"], N=256
)
cmap.set_bad(color="lightgray")

mean_df = df_mean[QMULTS[0]]
std_df = df_std[QMULTS[0]]
finite_values = mean_df.to_numpy(dtype=float)
finite_values = finite_values[np.isfinite(finite_values)]
if finite_values.size == 0:
    raise RuntimeError("No Experiment 9 retransmission-rate CSV data was found")

maximum_rate = float(np.max(finite_values))
norm = Normalize(vmin=0.0, vmax=maximum_rate if maximum_rate > 0 else 1.0)

fig, ax = plt.subplots(figsize=(10, 7))
image = ax.imshow(
    mean_df.values,
    origin="upper",
    aspect="auto",
    cmap=cmap,
    norm=norm,
    interpolation="nearest",
)

ax.set_xticks(np.arange(len(protocols)))
ax.set_xticklabels(
    [PROTOCOL_LABELS[protocol] for protocol in protocols],
    **HEATMAP_PROTOCOL_TICK_STYLE,
)
ax.set_yticks(np.arange(len(row_labels)))
ax.tick_params(axis="y", which="both", labelleft=False)

for row in range(mean_df.shape[0]):
    for column in range(mean_df.shape[1]):
        mean = mean_df.iat[row, column]
        std = std_df.iat[row, column]
        annotation = (
            rf"${mean:.2f}\mathbin{{\pm}}{std:.2f}$"
            if np.isfinite(mean) and np.isfinite(std)
            else "N/A"
        )
        ax.text(
            column,
            row,
            annotation,
            ha="center",
            va="center",
            color="black",
            fontsize=23,
        )

colorbar_axis = fig.add_axes([0.90, 0.15, 0.025, 0.83])
colorbar = fig.colorbar(image, cax=colorbar_axis)
colorbar.set_label(
    "Average Retransmission Rate (Mbps)",
    rotation=90,
    fontsize=24,
    labelpad=18,
)
colorbar.ax.tick_params(labelsize=27)
colorbar.ax.yaxis.set_label_position("right")
colorbar.ax.yaxis.tick_right()

plt.subplots_adjust(left=0.10, right=0.84, top=0.98, bottom=0.15)
fig.savefig("heatmap_retransmission_rate.pdf", dpi=1080, bbox_inches="tight")
plt.close(fig)
