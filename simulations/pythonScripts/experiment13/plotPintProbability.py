#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
import scienceplots

plt.style.use("science")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experiment13Support import MSS_BYTES, PINT_VARIANTS, RUNS, VARIANTS, WORKLOADS, workload_label
from plotDataExport import export_plot_dataframe
from plotProtocolSupport import (
    FINAL_ORBCC_LABEL,
    FULL_INT_REFERENCE_LABEL,
    PROTOCOL_COLORS,
)


SIMULATIONS_DIR = SCRIPT_DIR.parents[1]
CSV_ROOT = SIMULATIONS_DIR / "paperExperiments" / "experiment13" / "csvs"
SCENARIO_ROOT = SIMULATIONS_DIR / "paperExperiments" / "scenarios" / "experiment13"
PLOT_ROOT = SIMULATIONS_DIR / "plots" / "experiment13"

CLIENT_CONNECTION = "singledumbbell.client.tcp.conn"
SERVER_APPLICATION = "singledumbbell.server.app[0]"
RESPONSE_METRICS = ("cwnd", "goodput", "rtt", "U", "tau")
METRIC_SOURCES = {
    "cwnd": CLIENT_CONNECTION,
    "rtt": CLIENT_CONNECTION,
    "U": CLIENT_CONNECTION,
    "tau": CLIENT_CONNECTION,
    "goodput": SERVER_APPLICATION,
}
METRIC_LABELS = {
    "cwnd": "CWND (MSS)",
    "goodput": "Goodput (Mbps)",
    "rtt": "RTT (ms)",
    "U": "U",
    "tau": "Tau (ms)",
}
COLORS = {
    "orbtcp": PROTOCOL_COLORS["orbtcp"],
    "orbtcp_pint_p100": PROTOCOL_COLORS["orbtcp_pint"],
    "orbtcp_pint_p50": "#0077b6",
    "orbtcp_pint_p25": "#3a86ff",
    "orbtcp_pint_p12_5": "#8338ec",
    "orbtcp_pint_p6_25": "#c1121f",
    "orbtcp_pint_p3_125": "#e85d04",
    "orbtcp_pint_p1_5625": "#f48c06",
    "orbtcp_pint_p0_78125": "#9d4edd",
}


def metric_path(variant, workload: str, run: int, metric: str) -> Path:
    return (
        CSV_ROOT
        / variant.key
        / workload
        / f"run{run}"
        / METRIC_SOURCES[metric]
        / f"{metric}.csv"
    )


def load_metric(variant, workload: str, run: int, metric: str) -> pd.DataFrame:
    path = metric_path(variant, workload, run, metric)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {metric} data for {variant.key} run{run}: {path}")
    frame = pd.read_csv(path, usecols=["time", metric])
    frame["time"] = pd.to_numeric(frame["time"], errors="coerce")
    frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    return frame.dropna().sort_values("time")


def scale_metric(metric: str, values: pd.Series) -> tuple[pd.Series, str]:
    if metric == "cwnd":
        return values / MSS_BYTES, "MSS"
    if metric == "goodput":
        return values / 1_000_000, "Mbps"
    if metric in {"rtt", "tau"}:
        return values * 1000, "ms"
    return values, "ratio"


def response_event_times(workload: str, run: int) -> list[float]:
    scenario_file = SCENARIO_ROOT / f"{workload}_run{run}.json"
    data = json.loads(scenario_file.read_text(encoding="utf-8"))
    return [float(event["time_s"]) for event in data["events"] if event["time_s"] > 0]


def plot_individual_response(workload: str, run: int) -> None:
    run_dir = PLOT_ROOT / workload / f"run{run}"
    run_dir.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(len(RESPONSE_METRICS), 1, figsize=(11.5, 13.5), sharex=True)
    plotted_rows = []

    for axis, metric in zip(axes, RESPONSE_METRICS):
        for variant in VARIANTS:
            frame = load_metric(variant, workload, run, metric)
            values, unit = scale_metric(metric, frame[metric])
            axis.plot(
                frame["time"],
                values,
                color=COLORS[variant.key],
                linewidth=1.6 if variant.key == "orbtcp" else 1.1,
                alpha=1.0 if variant.key == "orbtcp" else 0.9,
                label=variant.label,
            )
            plotted_rows.extend(
                {
                    "workload": workload,
                    "run": run,
                    "variant": variant.key,
                    "variant_label": variant.label,
                    "pint_feedback_probability": variant.probability,
                    "metric": metric,
                    "unit": unit,
                    "time_s": time_s,
                    "value": value,
                }
                for time_s, value in zip(frame["time"], values)
            )
        for event_time in response_event_times(workload, run):
            axis.axvline(event_time, color="#777777", linestyle=":", linewidth=0.7, alpha=0.55)
        axis.set_ylabel(METRIC_LABELS[metric])
        axis.grid(True, alpha=0.22, linewidth=0.6)

    axes[-1].set_xlabel("Time (s)")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=8)
    figure.suptitle(
        f"Experiment 13: OrbCC feedback probability / "
        f"{workload_label(workload)} / Run {run}",
        y=0.995,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.93))
    figure.savefig(run_dir / "pint_probability_response.pdf", dpi=600, bbox_inches="tight")
    plt.close(figure)

    export_plot_dataframe(
        "response_points.csv",
        pd.DataFrame(plotted_rows),
        base_dir=run_dir / "plot_data",
        metadata={
            "experiment": "experiment13",
            "workload": workload,
            "run": run,
            "plot": "pint_probability_response",
            "description": "All final time-series points shown in the per-run response PDF. Dotted vertical lines mark completed handovers.",
        },
    )


def reporting_mean(frame: pd.DataFrame, metric: str) -> float:
    values, _unit = scale_metric(metric, frame[metric])
    second_averages = pd.DataFrame({"time": frame["time"], "value": values})
    second_averages["second"] = second_averages["time"].astype(int)
    return float(second_averages.groupby("second")["value"].mean().mean())


def collect_summary(workload: str) -> pd.DataFrame:
    rows = []
    for variant in VARIANTS:
        for metric in RESPONSE_METRICS:
            run_values = []
            for run in RUNS:
                run_values.append(reporting_mean(load_metric(variant, workload, run, metric), metric))
            _unused, unit = scale_metric(metric, pd.Series(run_values, dtype=float))
            rows.append(
                {
                    "workload": workload,
                    "variant": variant.key,
                    "variant_label": variant.label,
                    "pint_feedback_probability": variant.probability,
                    "metric": metric,
                    "unit": unit,
                    "mean": float(np.mean(run_values)),
                    "std": float(np.std(run_values)),
                    "run_values": np.asarray(run_values),
                }
            )
    return pd.DataFrame(rows)


def plot_probability_summary(workload: str, summary: pd.DataFrame) -> None:
    out_dir = PLOT_ROOT / workload / "cumulative"
    out_dir.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(len(RESPONSE_METRICS), 1, figsize=(8.4, 13.2), sharex=True)

    for axis, metric in zip(axes, RESPONSE_METRICS):
        metric_rows = summary[summary["metric"] == metric]
        reference = metric_rows[metric_rows["variant"] == "orbtcp"].iloc[0]
        pint_rows = metric_rows[metric_rows["variant"] != "orbtcp"].sort_values("pint_feedback_probability")
        axis.axhline(
            reference["mean"],
            color=COLORS["orbtcp"],
            linewidth=1.5,
            label=FULL_INT_REFERENCE_LABEL,
        )
        axis.fill_between(
            [pint_rows["pint_feedback_probability"].min(), pint_rows["pint_feedback_probability"].max()],
            reference["mean"] - reference["std"],
            reference["mean"] + reference["std"],
            color=COLORS["orbtcp"],
            alpha=0.10,
        )
        axis.errorbar(
            pint_rows["pint_feedback_probability"],
            pint_rows["mean"],
            yerr=pint_rows["std"],
            color=COLORS["orbtcp_pint_p100"],
            marker="o",
            markersize=4,
            linewidth=1.3,
            capsize=2,
            label=FINAL_ORBCC_LABEL,
        )
        axis.set_xscale("log", base=2)
        axis.set_ylabel(METRIC_LABELS[metric])
        axis.grid(True, which="both", alpha=0.22, linewidth=0.6)
        if metric == "cwnd":
            axis.legend(frameon=False, loc="best")

    axes[-1].set_xlabel("Feedback probability")
    axes[-1].xaxis.set_major_formatter(PercentFormatter(xmax=1))
    figure.suptitle(
        f"Experiment 13: OrbCC feedback probability / "
        f"{workload_label(workload)}",
        y=0.995,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.98))
    figure.savefig(out_dir / "pint_probability_summary.pdf", dpi=600, bbox_inches="tight")
    plt.close(figure)

    export_plot_dataframe(
        "pint_probability_summary_points.csv",
        summary,
        base_dir=out_dir / "plot_data",
        metadata={
            "experiment": "experiment13",
            "workload": workload,
            "plot": "pint_probability_summary",
            "description": "Each PINT point is the mean of per-second averages from five matched runs; error bars and full-INT band are population standard deviations across those runs.",
            "full_int_reference": "OrbCC with full INT, shown as a horizontal mean line and one-standard-deviation band.",
            "pint_probability_range": [variant.probability for variant in PINT_VARIANTS],
        },
    )


def main() -> None:
    for workload in WORKLOADS:
        for run in RUNS:
            plot_individual_response(workload, run)
        plot_probability_summary(workload, collect_summary(workload))


if __name__ == "__main__":
    main()
