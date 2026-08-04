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

from experimentTuningSupport import (
    BANDWIDTH_MBPS,
    EVALUATION_END_S,
    EVALUATION_START_S,
    EXPERIMENT,
    FAMILIES,
    FLOW_COUNTS,
    FULL_ORBCC,
    MSS_BYTES,
    RTT_MS,
    RUNS,
    VARIANTS,
    family_label,
    family_tick_labels,
    family_variant_series,
    family_x_label,
)
from plotDataExport import export_plot_dataframe
from plotProtocolSupport import PROTOCOL_COLORS


SIMULATIONS_DIR = SCRIPT_DIR.parents[1]
CSV_ROOT = SIMULATIONS_DIR / "paperExperiments" / EXPERIMENT / "csvs"
PLOT_ROOT = SIMULATIONS_DIR / "plots" / EXPERIMENT / "cumulative"
SECONDS = pd.Index(
    range(EVALUATION_START_S, EVALUATION_END_S), name="second"
)

PINT_COLOR = "#0C5DA5"
EXACT_COUNT_COLOR = "#00A087"
ORBIT_COLOR = PROTOCOL_COLORS["orbtcp"]
METRICS = (
    ("normalized_goodput", "Normalized goodput"),
    ("mean_queue_delay_ms", "Queueing delay (ms)"),
    ("jain_fairness", "Jain fairness"),
)


def metric_path(
    variant_key: str,
    flow_count: int,
    run: int,
    module: str,
    metric: str,
) -> Path:
    return (
        CSV_ROOT
        / variant_key
        / f"{flow_count}flows"
        / f"run{run}"
        / module
        / f"{metric}.csv"
    )


def load_per_second(path: Path, metric: str) -> pd.Series:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {metric} input: {path}")

    frame = pd.read_csv(path, usecols=["time", metric])
    frame["time"] = pd.to_numeric(frame["time"], errors="coerce")
    frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    frame = frame.dropna()
    if frame.empty or not (frame["time"] < EVALUATION_END_S).any():
        raise RuntimeError(
            f"No usable {metric} samples before reporting-window end: {path}"
        )

    frame["second"] = np.floor(frame["time"]).astype(int)
    values = frame.groupby("second")[metric].mean()
    expanded_index = values.index.union(SECONDS)
    values = values.reindex(expanded_index).sort_index().ffill().bfill().reindex(SECONDS)
    if values.isna().any():
        raise RuntimeError(f"Unable to fill reporting-window samples: {path}")
    return values


def jain_index(values: np.ndarray) -> float:
    denominator = len(values) * np.square(values).sum()
    return float(np.square(values.sum()) / denominator) if denominator > 0 else 0.0


def collect_run_metrics(variant, flow_count: int, run: int) -> dict[str, object]:
    flow_goodputs = []
    flow_rtts = []
    for flow_index in range(flow_count):
        goodput_module = f"singledumbbell.server[{flow_index}].app[0]"
        rtt_module = f"singledumbbell.client[{flow_index}].tcp.conn"
        flow_goodputs.append(
            load_per_second(
                metric_path(
                    variant.key,
                    flow_count,
                    run,
                    goodput_module,
                    "goodput",
                ),
                "goodput",
            )
        )
        flow_rtts.append(
            load_per_second(
                metric_path(
                    variant.key,
                    flow_count,
                    run,
                    rtt_module,
                    "rtt",
                ),
                "rtt",
            )
        )

    goodput_frame = pd.concat(flow_goodputs, axis=1)
    rtt_frame = pd.concat(flow_rtts, axis=1)
    aggregate_goodput = goodput_frame.sum(axis=1)
    flow_mean_goodputs = goodput_frame.mean(axis=0).to_numpy(dtype=float)

    queue_module = f"singledumbbell.router1.ppp[{flow_count}].queue"
    queue_packets = load_per_second(
        metric_path(
            variant.key,
            flow_count,
            run,
            queue_module,
            "queueLength",
        ),
        "queueLength",
    )
    queue_delay_ms = (
        queue_packets * MSS_BYTES * 8 / (BANDWIDTH_MBPS * 1_000_000) * 1000
    )

    return {
        "variant": variant.key,
        "variant_label": variant.label,
        "family": variant.family,
        "flow_count": flow_count,
        "run": run,
        "flow_count_bits": variant.flow_count_bits,
        "flow_count_sketch": variant.flow_count_sketch,
        "utilization_bits": variant.utilization_bits,
        "feedback_probability": variant.feedback_probability,
        "normalized_goodput": float(
            aggregate_goodput.mean() / (BANDWIDTH_MBPS * 1_000_000)
        ),
        "normalized_rtt": float(
            rtt_frame.mean(axis=1).mean() / (RTT_MS / 1000)
        ),
        "jain_fairness": jain_index(flow_mean_goodputs),
        "mean_queue_delay_ms": float(queue_delay_ms.mean()),
        "p95_queue_delay_ms": float(queue_delay_ms.quantile(0.95)),
    }


def collect_all_runs() -> pd.DataFrame:
    rows = []
    for variant in VARIANTS:
        for flow_count in FLOW_COUNTS:
            for run in RUNS:
                rows.append(collect_run_metrics(variant, flow_count, run))
    return pd.DataFrame(rows)


def aggregate_runs(run_metrics: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [metric for metric, _label in METRICS]
    metric_columns.extend(("normalized_rtt", "p95_queue_delay_ms"))
    rows = []
    for (variant, flow_count), group in run_metrics.groupby(
        ["variant", "flow_count"], sort=False
    ):
        first = group.iloc[0]
        row = {
            "variant": variant,
            "variant_label": first["variant_label"],
            "family": first["family"],
            "flow_count": flow_count,
            "flow_count_bits": first["flow_count_bits"],
            "flow_count_sketch": first["flow_count_sketch"],
            "utilization_bits": first["utilization_bits"],
            "feedback_probability": first["feedback_probability"],
        }
        for metric in metric_columns:
            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_std"] = float(np.std(values))
            row[f"{metric}_runs"] = values
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_row(
    aggregate: pd.DataFrame, variant_key: str, flow_count: int
) -> pd.Series:
    rows = aggregate[
        (aggregate["variant"] == variant_key)
        & (aggregate["flow_count"] == flow_count)
    ]
    if len(rows) != 1:
        raise RuntimeError(
            f"Expected one aggregate row for {variant_key}/{flow_count}flows, "
            f"found {len(rows)}"
        )
    return rows.iloc[0]


def plot_family(family: str, aggregate: pd.DataFrame) -> None:
    variant_series = family_variant_series(family)
    tick_labels = family_tick_labels(family)
    x_values = np.arange(len(tick_labels))
    series_styles = (
        (PINT_COLOR, "o"),
        (EXACT_COUNT_COLOR, "^"),
    )
    figure, axes = plt.subplots(
        len(METRICS),
        len(FLOW_COUNTS),
        figsize=(11.2, 7.4),
        sharex="col",
        squeeze=False,
    )

    for column, flow_count in enumerate(FLOW_COUNTS):
        axes[0, column].set_title(f"{flow_count} flows")
        reference = aggregate_row(aggregate, FULL_ORBCC.key, flow_count)

        for row_index, (metric, metric_label) in enumerate(METRICS):
            axis = axes[row_index, column]
            reference_mean = float(reference[f"{metric}_mean"])
            reference_std = float(reference[f"{metric}_std"])

            exact_mean = None
            for series_index, (series_label, variants) in enumerate(variant_series):
                color, marker = series_styles[series_index]
                means = np.asarray(
                    [
                        aggregate_row(aggregate, variant.key, flow_count)[
                            f"{metric}_mean"
                        ]
                        for variant in variants
                    ],
                    dtype=float,
                )
                errors = np.asarray(
                    [
                        aggregate_row(aggregate, variant.key, flow_count)[
                            f"{metric}_std"
                        ]
                        for variant in variants
                    ],
                    dtype=float,
                )
                exact_mean = means[-1]
                axis.errorbar(
                    x_values,
                    means,
                    yerr=errors,
                    color=color,
                    marker=marker,
                    markersize=4.5,
                    linewidth=1.4,
                    capsize=2.5,
                    label=series_label,
                )

            axis.scatter(
                [x_values[-1]],
                [exact_mean],
                color="#303030",
                marker="s",
                s=35,
                zorder=4,
            )
            axis.axhline(
                reference_mean,
                color=ORBIT_COLOR,
                linestyle="--",
                linewidth=1.35,
                label="OrbCC (full INT)",
            )
            axis.fill_between(
                [x_values[0], x_values[-1]],
                reference_mean - reference_std,
                reference_mean + reference_std,
                color=ORBIT_COLOR,
                alpha=0.10,
            )
            axis.grid(True, alpha=0.22, linewidth=0.6)
            axis.set_xticks(x_values, tick_labels)
            if column == 0:
                axis.set_ylabel(metric_label)
            if row_index == len(METRICS) - 1:
                axis.set_xlabel(family_x_label(family))
            if metric == "jain_fairness":
                axis.set_ylim(0, 1.02)
            elif metric == "mean_queue_delay_ms":
                axis.set_ylim(bottom=0)

    legend_handles = []
    for series_index, (series_label, _variants) in enumerate(variant_series):
        color, marker = series_styles[series_index]
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=color,
                marker=marker,
                linewidth=1.4,
                label=series_label,
            )
        )
    legend_handles.append(
        Line2D(
            [0],
            [0],
            color=ORBIT_COLOR,
            linestyle="--",
            linewidth=1.35,
            label="OrbCC (full INT)",
        )
    )
    figure.legend(
        handles=legend_handles,
        loc="upper center",
        ncol=len(legend_handles),
        frameon=False,
        bbox_to_anchor=(0.5, 0.985),
    )
    figure.suptitle(f"{family_label(family)} trade-off", y=1.025)
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    figure.savefig(
        PLOT_ROOT / f"{family}_tradeoff.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)

    selected_keys = {FULL_ORBCC.key}
    for _series_label, variants in variant_series:
        selected_keys.update(variant.key for variant in variants)
    export_plot_dataframe(
        f"{family}_tradeoff_points.csv",
        aggregate[aggregate["variant"].isin(selected_keys)],
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            "experiment": EXPERIMENT,
            "family": family,
            "description": (
                "Means, population standard deviations, and matched-run values "
                "used by the aggregate tuning plot. The flow-count plot separates "
                "sketch-derived and exact counts at every field width. Exact PINT "
                "is shared by all feature sweeps; OrbCC full INT is the dashed "
                "reference."
            ),
            "flow_counts": FLOW_COUNTS,
            "runs": list(RUNS),
            "reporting_window_seconds": [
                EVALUATION_START_S,
                EVALUATION_END_S,
            ],
        },
    )


def main() -> None:
    PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    run_metrics = collect_all_runs()
    aggregate = aggregate_runs(run_metrics)
    export_plot_dataframe(
        "all_run_metrics.csv",
        run_metrics,
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            "experiment": EXPERIMENT,
            "description": (
                "Per-run metrics after all flows have joined, including periodic "
                "hard handovers. Goodput includes handover downtime."
            ),
            "reporting_window_seconds": [EVALUATION_START_S, EVALUATION_END_S],
        },
    )
    export_plot_dataframe(
        "all_aggregate_metrics.csv",
        aggregate,
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            "experiment": EXPERIMENT,
            "description": "Five-run means and population standard deviations.",
        },
    )
    for family in FAMILIES:
        plot_family(family, aggregate)


if __name__ == "__main__":
    main()
