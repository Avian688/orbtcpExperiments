#!/usr/bin/env python3

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plotDataExport import export_plot_dataframe


MSS_BYTES = 1448
RUNS = 5
EVENTS = [
    (15, "BW x2"),
    (30, "BW /2"),
    (35, "RTT x2"),
    (60, "RTT /2"),
    (75, "1% loss"),
    (90, "loss off"),
]
PROTOCOLS = [
    ("bbr3", "BBRv3"),
    ("cubic", "Cubic"),
    ("bbr", "BBRv1"),
]
VARIANTS = [
    ("no_updated_sack_no_pacing_no_rack", "No updated SACK, no pacing, no RACK"),
    ("updated_sack_no_pacing_no_rack", "Updated SACK, no pacing, no RACK"),
    ("updated_sack_pacing_no_rack", "Updated SACK, pacing, no RACK"),
    ("all_enabled", "Updated SACK, pacing, RACK"),
]


def cwnd_file_for(run: int, protocol: str, variant: str) -> Path:
    return (
        Path("../../paperExperiments/experiment0/csvs")
        / protocol
        / variant
        / f"run{run}"
        / "singledumbbell.client[0].tcp.conn"
        / "cwnd.csv"
    )


def goodput_file_for(run: int, protocol: str, variant: str) -> Path:
    return (
        Path("../../paperExperiments/experiment0/csvs")
        / protocol
        / variant
        / f"run{run}"
        / "singledumbbell.server[0].app[0]"
        / "goodput.csv"
    )


def add_event_lines(ax, show_labels: bool) -> None:
    for event_time, label in EVENTS:
        ax.axvline(event_time, color="0.65", linewidth=0.8, linestyle="--")
        if show_labels:
            ymax = ax.get_ylim()[1]
            ax.text(event_time, ymax, label, rotation=90, va="top", ha="right", fontsize=8, color="0.3")


def plot_cwnd_run(run: int, protocol: str, protocol_label: str, out_dir: Path) -> list[pd.DataFrame]:
    fig, axes = plt.subplots(len(VARIANTS), 1, figsize=(12, 2.35 * len(VARIANTS)), sharex=True)
    fig.suptitle(f"Experiment 0 {protocol_label} CWND comparison, run {run}", fontsize=14)
    plotted_dataframes = []

    for index, (variant, title) in enumerate(VARIANTS):
        ax = axes[index]
        csv_path = cwnd_file_for(run, protocol, variant)
        ax.set_title(title, fontsize=10)
        ax.grid(True, linewidth=0.4, alpha=0.65)
        ax.set_ylabel("CWND (MSS)")

        if csv_path.is_file():
            data = pd.read_csv(csv_path)
            cwnd_mss = data["cwnd"] / MSS_BYTES
            ax.plot(data["time"], cwnd_mss, drawstyle="steps-post", linewidth=1.1)
            plotted_dataframes.append(pd.DataFrame({
                "run": run,
                "protocol": protocol,
                "protocol_label": protocol_label,
                "variant": variant,
                "variant_label": title,
                "time_s": data["time"],
                "cwnd_bytes": data["cwnd"],
                "cwnd_mss": cwnd_mss,
            }))
        else:
            ax.text(0.5, 0.5, f"Missing {csv_path}", transform=ax.transAxes, ha="center", va="center")

        add_event_lines(ax, show_labels=index == 0)

    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_dir / "cwnd_comparison.pdf", bbox_inches="tight")
    plt.close(fig)
    return plotted_dataframes


def plot_goodput_run(run: int, protocol: str, protocol_label: str, out_dir: Path) -> list[pd.DataFrame]:
    fig, axes = plt.subplots(len(VARIANTS), 1, figsize=(12, 2.35 * len(VARIANTS)), sharex=True)
    fig.suptitle(f"Experiment 0 {protocol_label} goodput comparison, run {run}", fontsize=14)
    plotted_dataframes = []

    for index, (variant, title) in enumerate(VARIANTS):
        ax = axes[index]
        csv_path = goodput_file_for(run, protocol, variant)
        ax.set_title(title, fontsize=10)
        ax.grid(True, linewidth=0.4, alpha=0.65)
        ax.set_ylabel("Goodput (Mbps)")

        if csv_path.is_file():
            data = pd.read_csv(csv_path)
            goodput_mbps = data["goodput"] / 1_000_000.0
            ax.plot(data["time"], goodput_mbps, linewidth=1.1)
            plotted_dataframes.append(pd.DataFrame({
                "run": run,
                "protocol": protocol,
                "protocol_label": protocol_label,
                "variant": variant,
                "variant_label": title,
                "time_s": data["time"],
                "goodput_bps": data["goodput"],
                "goodput_mbps": goodput_mbps,
            }))
        else:
            ax.text(0.5, 0.5, f"Missing {csv_path}", transform=ax.transAxes, ha="center", va="center")

        add_event_lines(ax, show_labels=index == 0)

    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_dir / "goodput_comparison.pdf", bbox_inches="tight")
    plt.close(fig)
    return plotted_dataframes


def plot_run(run: int, protocol: str, protocol_label: str) -> bool:
    out_dir = Path("../../plots/experiment0") / protocol / f"run{run}"
    out_dir.mkdir(parents=True, exist_ok=True)

    cwnd_dataframes = plot_cwnd_run(run, protocol, protocol_label, out_dir)
    goodput_dataframes = plot_goodput_run(run, protocol, protocol_label, out_dir)

    if cwnd_dataframes:
        export_plot_dataframe(
            "cwnd_comparison.csv",
            pd.concat(cwnd_dataframes, ignore_index=True),
            base_dir=out_dir / "plot_data",
            metadata={
                "experiment": "experiment0",
                "plot": "cwnd_comparison",
                "run": run,
                "protocol": protocol,
                "description": f"Complete plotted CWND time series for the four {protocol_label} feature configurations.",
            },
        )
    if goodput_dataframes:
        export_plot_dataframe(
            "goodput_comparison.csv",
            pd.concat(goodput_dataframes, ignore_index=True),
            base_dir=out_dir / "plot_data",
            metadata={
                "experiment": "experiment0",
                "plot": "goodput_comparison",
                "run": run,
                "protocol": protocol,
                "description": f"Complete plotted goodput time series for the four {protocol_label} feature configurations.",
            },
        )
    return bool(cwnd_dataframes or goodput_dataframes)


def main() -> int:
    plotted = False
    for protocol, protocol_label in PROTOCOLS:
        for run in range(1, RUNS + 1):
            plotted = plot_run(run, protocol, protocol_label) or plotted
    if not plotted:
        print("No CWND or goodput CSVs found yet. Run simulations/export/extraction first.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
