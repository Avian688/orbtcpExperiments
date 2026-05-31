#!/usr/bin/env python3

from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import numpy as np
import pandas as pd
import scienceplots

plt.style.use("science")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plotDataExport import export_plot_dataframe
from plotProtocolSupport import PROTOCOL_COLORS, PROTOCOL_LABELS


PROTOCOLS = ("cubic", "orca")
RUNS = range(1, 6)
BANDWIDTH_MBPS = 100
BASE_RTT_MS = 20
EVALUATION_START_S = 50
EVALUATION_END_S = 100
SIMULATIONS_DIR = Path(__file__).resolve().parents[2]
CSV_ROOT = SIMULATIONS_DIR / "paperExperiments" / "experiment12" / "csvs"
PLOT_DIR = SIMULATIONS_DIR / "plots" / "experiment12" / "cumulative"


def confidence_ellipse(x_values, y_values, axis, color):
    if len(x_values) < 2 or np.allclose(np.std(x_values), 0) or np.allclose(np.std(y_values), 0):
        return

    covariance = np.cov(x_values, y_values)
    pearson = covariance[0, 1] / np.sqrt(covariance[0, 0] * covariance[1, 1])
    pearson = np.clip(pearson, -1, 1)
    ellipse = Ellipse(
        (0, 0),
        width=2 * np.sqrt(1 + pearson),
        height=2 * np.sqrt(1 - pearson),
        facecolor=color,
        edgecolor="none",
        alpha=0.25,
    )
    transform = (
        transforms.Affine2D()
        .rotate_deg(45)
        .scale(np.sqrt(covariance[0, 0]), np.sqrt(covariance[1, 1]))
        .translate(np.mean(x_values), np.mean(y_values))
    )
    ellipse.set_transform(transform + axis.transData)
    axis.add_patch(ellipse)


def load_window_mean(csv_path: Path, column: str) -> float:
    frame = pd.read_csv(csv_path, usecols=["time", column])
    frame["time"] = pd.to_numeric(frame["time"], errors="coerce")
    frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().loc[
        lambda values: values["time"].between(EVALUATION_START_S, EVALUATION_END_S)
    ]
    if frame.empty:
        raise RuntimeError(f"No {column} samples in reporting window: {csv_path}")
    frame["second"] = frame["time"].astype(int)
    return float(frame.groupby("second")[column].mean().mean())


def collect_points() -> pd.DataFrame:
    rows = []
    for protocol in PROTOCOLS:
        delay_runs = []
        goodput_runs = []
        for run in RUNS:
            run_dir = CSV_ROOT / protocol / f"run{run}"
            goodput = load_window_mean(run_dir / "singledumbbell.server[0].app[0]" / "goodput.csv", "goodput")
            rtt = load_window_mean(run_dir / "singledumbbell.client[0].tcp.conn" / "rtt.csv", "rtt")
            rtt_ms = rtt * 1000 if rtt < 5 else rtt
            goodput_runs.append(goodput / 1_000_000 / BANDWIDTH_MBPS)
            delay_runs.append(rtt_ms / BASE_RTT_MS)

        rows.append(
            {
                "protocol": protocol,
                "x_normalised_delay": float(np.mean(delay_runs)),
                "y_normalised_goodput": float(np.mean(goodput_runs)),
                "xerr_normalised_delay_std": float(np.std(delay_runs)),
                "yerr_normalised_goodput_std": float(np.std(goodput_runs)),
                "x_runs_normalised_delay": np.asarray(delay_runs),
                "y_runs_normalised_goodput": np.asarray(goodput_runs),
            }
        )
    return pd.DataFrame(rows)


def plot(points: pd.DataFrame) -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    export_plot_dataframe(
        "efficiency_orca_vs_cubic_points.csv",
        points,
        base_dir=PLOT_DIR / "plot_data",
        metadata={
            "experiment": "experiment12",
            "plot": "efficiency_orca_vs_cubic",
            "description": "Efficiency scatter means and per-run values from the final 50 seconds.",
            "reporting_window_seconds": [EVALUATION_START_S, EVALUATION_END_S],
        },
    )

    figure, axis = plt.subplots(figsize=(4.5, 2.2))
    axis.grid(True, which="major", alpha=0.2, linewidth=0.6)
    for _, row in points.iterrows():
        protocol = row["protocol"]
        color = PROTOCOL_COLORS[protocol]
        confidence_ellipse(
            row["x_runs_normalised_delay"],
            row["y_runs_normalised_goodput"],
            axis,
            color,
        )
        axis.scatter(
            row["x_normalised_delay"],
            row["y_normalised_goodput"],
            marker="o",
            s=60,
            facecolors="none",
            edgecolors=color,
            linewidths=1.2,
        )

    axis.legend(
        handles=[
            Line2D([0], [0], color=PROTOCOL_COLORS[protocol], lw=1.5, label=PROTOCOL_LABELS[protocol])
            for protocol in PROTOCOLS
        ],
        frameon=False,
        loc="best",
    )
    axis.set_xlabel("Normalised Delay")
    axis.set_ylabel("Normalised Goodput")
    axis.invert_xaxis()
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "efficiency_orca_vs_cubic.pdf", dpi=1080, bbox_inches="tight")
    plt.close(figure)


if __name__ == "__main__":
    plot(collect_points())
