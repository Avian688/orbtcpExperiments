#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import scienceplots

plt.style.use(["science", "no-latex"])

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experimentTuningSupport import (  # noqa: E402
    EXPERIMENT,
    FLOW_COUNTS,
    MSS_BYTES,
    RTT_MS,
    RUNS,
    SIMULATION_TIME_S,
    VARIANTS,
    bottleneck_bandwidth_mbps,
)
from plotProtocolSupport import PROTOCOL_COLORS  # noqa: E402


SIMULATIONS_DIR = SCRIPT_DIR.parents[1]
CSV_ROOT = SIMULATIONS_DIR / "paperExperiments" / EXPERIMENT / "csvs"
PLOT_ROOT = SIMULATIONS_DIR / "plots" / EXPERIMENT / "individual"
RUN_TO_PLOT = 1
SECONDS = pd.Index(range(SIMULATION_TIME_S), name="time")

FLOW_COLOR = "#0C5DA5"
REFERENCE_COLOR = "#777777"
GOODPUT_COLOR = PROTOCOL_COLORS["orbtcp"]


def metric_path(
    variant_key: str,
    flow_count: int,
    flow_index: int,
    metric: str,
) -> Path:
    module = (
        f"singledumbbell.server[{flow_index}].app[0]"
        if metric == "goodput"
        else f"singledumbbell.client[{flow_index}].tcp.conn"
    )
    return (
        CSV_ROOT
        / variant_key
        / f"{flow_count}flows"
        / f"run{RUN_TO_PLOT}"
        / module
        / f"{metric}.csv"
    )


def read_metric(path: Path, metric: str) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Missing Run {RUN_TO_PLOT} {metric}: {path}")

    frame = pd.read_csv(path, usecols=["time", metric])
    frame["time"] = pd.to_numeric(frame["time"], errors="coerce")
    frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    frame = frame.dropna().sort_values("time")
    frame = frame[
        (frame["time"] >= 0) & (frame["time"] <= SIMULATION_TIME_S)
    ]
    if frame.empty:
        raise RuntimeError(f"No usable Run {RUN_TO_PLOT} {metric}: {path}")
    return frame


def load_goodput(variant_key: str, flow_count: int, flow_index: int) -> pd.Series:
    frame = read_metric(
        metric_path(variant_key, flow_count, flow_index, "goodput"),
        "goodput",
    )
    frame["second"] = np.floor(frame["time"]).astype(int)
    frame = frame[
        (frame["second"] >= 0) & (frame["second"] < SIMULATION_TIME_S)
    ]
    values = frame.groupby("second")["goodput"].mean()
    return values.reindex(SECONDS).ffill().fillna(0.0)


def plot_flow_metric(
    axis,
    frames: list[pd.DataFrame],
    metric: str,
    scale: float,
    ylabel: str,
    extra_legend_handles: tuple[Line2D, ...] = (),
) -> None:
    line_alpha = max(0.10, min(0.65, 3.0 / np.sqrt(len(frames))))
    for frame in frames:
        axis.plot(
            frame["time"],
            frame[metric] * scale,
            color=FLOW_COLOR,
            alpha=line_alpha,
            linewidth=0.75,
            drawstyle="steps-post",
        )
    axis.set_ylabel(ylabel)
    axis.set_ylim(bottom=0)
    axis.legend(
        handles=(
            Line2D([0], [0], color=FLOW_COLOR, linewidth=1.0, label="Flows"),
            *extra_legend_handles,
        ),
        loc="upper right",
        frameon=False,
    )


def plot_configuration(variant, flow_count: int) -> None:
    bandwidth_mbps = bottleneck_bandwidth_mbps(flow_count)
    goodputs = [
        load_goodput(variant.key, flow_count, flow_index)
        for flow_index in range(flow_count)
    ]
    aggregate_goodput_mbps = (
        pd.concat(goodputs, axis=1).sum(axis=1) / 1_000_000
    )
    cwnd_frames = [
        read_metric(
            metric_path(variant.key, flow_count, flow_index, "cwnd"),
            "cwnd",
        )
        for flow_index in range(flow_count)
    ]
    rtt_frames = [
        read_metric(
            metric_path(variant.key, flow_count, flow_index, "rtt"),
            "rtt",
        )
        for flow_index in range(flow_count)
    ]

    figure, axes = plt.subplots(
        3,
        1,
        figsize=(11.4, 8.2),
        sharex=True,
        squeeze=False,
    )
    goodput_axis, cwnd_axis, rtt_axis = axes[:, 0]

    goodput_axis.plot(
        aggregate_goodput_mbps.index,
        aggregate_goodput_mbps,
        color=GOODPUT_COLOR,
        linewidth=1.45,
        label="Aggregate goodput",
    )
    goodput_axis.axhline(
        bandwidth_mbps,
        color=REFERENCE_COLOR,
        linestyle="--",
        linewidth=1.2,
        label="Link capacity",
    )
    goodput_axis.set_ylabel("Goodput (Mbps)")
    goodput_axis.set_ylim(bottom=0)
    goodput_axis.legend(loc="upper right", frameon=False)

    plot_flow_metric(
        cwnd_axis,
        cwnd_frames,
        "cwnd",
        1.0 / MSS_BYTES,
        "CWND (MSS)",
    )
    rtt_axis.axhline(
        RTT_MS,
        color=REFERENCE_COLOR,
        linestyle="--",
        linewidth=1.2,
        label="Base RTT",
    )
    plot_flow_metric(
        rtt_axis,
        rtt_frames,
        "rtt",
        1000.0,
        "RTT (ms)",
        extra_legend_handles=(
            Line2D(
                [0],
                [0],
                color=REFERENCE_COLOR,
                linestyle="--",
                linewidth=1.2,
                label="Base RTT",
            ),
        ),
    )

    for axis in (goodput_axis, cwnd_axis, rtt_axis):
        axis.set_xlim(0, SIMULATION_TIME_S)
        axis.grid(True, alpha=0.22, linewidth=0.6)
        axis.set_xlabel("Time (s)")

    figure.suptitle(
        f"{variant.label}: {flow_count} flows, {bandwidth_mbps} Mbps, "
        f"Run {RUN_TO_PLOT}",
        y=0.995,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.975))

    output_dir = (
        PLOT_ROOT
        / variant.key
        / f"{flow_count}flows"
        / f"run{RUN_TO_PLOT}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_dir / "timeseries.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)


def main() -> None:
    if RUN_TO_PLOT not in RUNS:
        raise RuntimeError(f"Individual plot run {RUN_TO_PLOT} is not in RUNS")

    for variant in VARIANTS:
        for flow_count in FLOW_COUNTS:
            plot_configuration(variant, flow_count)


if __name__ == "__main__":
    main()
