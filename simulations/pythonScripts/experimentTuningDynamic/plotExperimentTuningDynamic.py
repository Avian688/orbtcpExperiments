#!/usr/bin/env python3

from __future__ import annotations

from itertools import groupby
import json
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

from experimentTuningDynamicSupport import (  # noqa: E402
    CONDITIONS,
    EXACT_PINT,
    EXPERIMENT,
    FAMILIES,
    FLOW_COUNT_EXACT_VARIANTS,
    FLOW_COUNT_SKETCH_VARIANTS,
    FLOW_COUNTS,
    FULL_ORBCC,
    MSS_BYTES,
    RUNS,
    SIMULATION_TIME_S,
    VARIANTS,
    Variant,
    family_label,
    family_plot_variants,
    family_tick_labels,
    family_variant_series,
    family_x_label,
    trace_name,
)
from plotDataExport import export_plot_dataframe  # noqa: E402
from plotProtocolSupport import PROTOCOL_COLORS  # noqa: E402


SIMULATIONS_DIR = SCRIPT_DIR.parents[1]
CSV_ROOT = SIMULATIONS_DIR / "paperExperiments" / EXPERIMENT / "csvs"
SCENARIO_ROOT = (
    SIMULATIONS_DIR / "paperExperiments" / "scenarios" / EXPERIMENT
)
PLOT_ROOT = SIMULATIONS_DIR / "plots" / EXPERIMENT / "cumulative"
SECONDS = pd.Index(range(SIMULATION_TIME_S), name="second")

METRICS = (
    (
        "aggregate_goodput_mbps",
        "Average aggregate goodput (Mbps)",
        "goodput",
    ),
    (
        "mean_queue_delay_ms",
        "Average queueing delay (ms)",
        "queueing_delay",
    ),
    (
        "aggregate_retransmission_mbps",
        "Average aggregate retransmission rate (Mbps)",
        "retransmissions",
    ),
)
TRADEOFF_METRICS = (
    ("normalized_goodput", "Normalized goodput"),
    ("mean_queue_delay_ms", "Queueing delay (ms)"),
    ("aggregate_retransmission_mbps", "Retransmission rate (Mbps)"),
)

BIT_COLORS = {
    4: "#0C5DA5",
    6: "#00A087",
    8: "#D1495B",
    10: "#7E2F8E",
}
SERIES_COLORS = ("#0C5DA5", "#00A087", "#D1495B", "#7E2F8E")
AVAILABLE_CAPACITY_COLOR = "#777777"
PINT_COLOR = "#0C5DA5"
EXACT_COUNT_COLOR = "#00A087"
MATCHED_RUN_ALPHA = 0.12


def metric_path(
    variant_key: str,
    condition_key: str,
    flow_count: int,
    run: int,
    module: str,
    metric: str,
) -> Path:
    return (
        CSV_ROOT
        / variant_key
        / condition_key
        / f"{flow_count}flows"
        / f"run{run}"
        / module
        / f"{metric}.csv"
    )


def read_vector(path: Path, metric: str) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {metric} input: {path}")
    frame = pd.read_csv(path, usecols=["time", metric])
    frame["time"] = pd.to_numeric(frame["time"], errors="coerce")
    frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    frame = frame.dropna().sort_values("time")
    frame = frame[
        (frame["time"] >= 0) & (frame["time"] <= SIMULATION_TIME_S)
    ]
    if frame.empty:
        raise RuntimeError(f"No usable {metric} samples: {path}")
    return frame


def load_interval_rate(path: Path, metric: str) -> pd.Series:
    frame = read_vector(path, metric)
    # Each rate sample describes the interval ending at its timestamp.
    frame["second"] = np.ceil(frame["time"] - 1e-9).astype(int) - 1
    frame = frame[(frame["second"] >= 0) & (frame["second"] < SIMULATION_TIME_S)]
    values = frame.groupby("second")[metric].mean()
    return values.reindex(SECONDS).ffill().fillna(0.0)


def load_trace(run: int) -> dict:
    path = SCENARIO_ROOT / f"{trace_name(run)}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing dynamic trace: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def path_and_queue_means(queue_frame: pd.DataFrame, trace: dict) -> tuple[float, float]:
    states = trace["states"]
    current_bandwidth = float(states[0]["bandwidth_mbps"])
    current_queue_packets = 0.0
    available = True

    # Path events are applied before queue events at the same timestamp.
    events: list[tuple[float, int, str, float]] = []
    for state in states[1:]:
        events.append(
            (float(state["handover_time_s"]), 0, "disconnect", 0.0)
        )
        events.append(
            (
                float(state["reconnect_time_s"]),
                0,
                "reconnect",
                float(state["bandwidth_mbps"]),
            )
        )
    for row in queue_frame.itertuples(index=False):
        events.append((float(row.time), 1, "queue", max(0.0, float(row.queueLength))))
    events.sort(key=lambda event: (event[0], event[1]))

    queue_delay_area_ms_s = 0.0
    available_capacity_area_mbit = 0.0
    previous_time = 0.0

    def accumulate(until: float) -> None:
        nonlocal previous_time, queue_delay_area_ms_s, available_capacity_area_mbit
        until = min(max(until, previous_time), float(SIMULATION_TIME_S))
        duration = until - previous_time
        if duration > 0 and available:
            queue_delay_ms = (
                current_queue_packets
                * MSS_BYTES
                * 8
                / (current_bandwidth * 1_000_000)
                * 1000
            )
            queue_delay_area_ms_s += queue_delay_ms * duration
            available_capacity_area_mbit += current_bandwidth * duration
        previous_time = until

    for event_time, grouped_events in groupby(events, key=lambda event: event[0]):
        if event_time > SIMULATION_TIME_S:
            break
        accumulate(event_time)
        for _time, _priority, kind, value in grouped_events:
            if kind == "disconnect":
                available = False
                current_queue_packets = 0.0
            elif kind == "reconnect":
                current_bandwidth = value
                current_queue_packets = 0.0
                available = True
            else:
                current_queue_packets = value

    accumulate(float(SIMULATION_TIME_S))
    return (
        queue_delay_area_ms_s / SIMULATION_TIME_S,
        available_capacity_area_mbit / SIMULATION_TIME_S,
    )


def collect_run_metrics(
    variant: Variant,
    flow_count: int,
    condition,
    run: int,
) -> dict[str, object]:
    goodput_series = []
    retransmission_series = []
    for flow_index in range(flow_count):
        goodput_series.append(
            load_interval_rate(
                metric_path(
                    variant.key,
                    condition.key,
                    flow_count,
                    run,
                    f"singledumbbell.server[{flow_index}].app[0]",
                    "goodput",
                ),
                "goodput",
            )
        )
        retransmission_series.append(
            load_interval_rate(
                metric_path(
                    variant.key,
                    condition.key,
                    flow_count,
                    run,
                    f"singledumbbell.client[{flow_index}].tcp.conn",
                    "retransmissionRate",
                ),
                "retransmissionRate",
            )
        )

    aggregate_goodput_bps = pd.concat(goodput_series, axis=1).sum(axis=1)
    aggregate_retransmission_bps = pd.concat(
        retransmission_series, axis=1
    ).sum(axis=1)
    queue_frame = read_vector(
        metric_path(
            variant.key,
            condition.key,
            flow_count,
            run,
            f"singledumbbell.router1.ppp[{flow_count}].queue",
            "queueLength",
        ),
        "queueLength",
    )
    mean_queue_delay_ms, mean_available_capacity_mbps = path_and_queue_means(
        queue_frame, load_trace(run)
    )
    aggregate_goodput_mbps = float(aggregate_goodput_bps.mean() / 1_000_000)

    return {
        "variant": variant.key,
        "variant_label": variant.label,
        "family": variant.family,
        "flow_count": flow_count,
        "condition": condition.key,
        "condition_label": condition.label,
        "run": run,
        "flow_count_bits": variant.flow_count_bits,
        "flow_count_sketch": variant.flow_count_sketch,
        "utilization_bits": variant.utilization_bits,
        "feedback_probability": variant.feedback_probability,
        "aggregate_goodput_mbps": aggregate_goodput_mbps,
        "mean_available_capacity_mbps": mean_available_capacity_mbps,
        "normalized_goodput": (
            aggregate_goodput_mbps / mean_available_capacity_mbps
            if mean_available_capacity_mbps > 0
            else 0.0
        ),
        "mean_queue_delay_ms": mean_queue_delay_ms,
        "aggregate_retransmission_mbps": float(
            aggregate_retransmission_bps.mean() / 1_000_000
        ),
    }


def collect_all_runs() -> pd.DataFrame:
    rows = []
    for variant in VARIANTS:
        for flow_count in FLOW_COUNTS:
            for condition in CONDITIONS:
                for run in RUNS:
                    rows.append(
                        collect_run_metrics(variant, flow_count, condition, run)
                    )
    return pd.DataFrame(rows)


def variant_display_label(variant: Variant) -> str:
    if variant == FULL_ORBCC:
        return "OrbCC (full INT)"
    if variant == EXACT_PINT:
        return "Exact PINT"
    if variant in FLOW_COUNT_SKETCH_VARIANTS:
        return f"Sketch, {variant.flow_count_bits} bits"
    if variant in FLOW_COUNT_EXACT_VARIANTS:
        return f"Exact count, {variant.flow_count_bits} bits"
    return variant.label


def variant_style(variant: Variant, family: str) -> dict[str, object]:
    if variant == FULL_ORBCC:
        return {
            "color": PROTOCOL_COLORS["orbtcp"],
            "linestyle": ":",
            "linewidth": 2.0,
        }
    if variant == EXACT_PINT:
        return {"color": "#303030", "linestyle": "--", "linewidth": 2.0}
    if family == "flow_count":
        return {
            "color": BIT_COLORS[int(variant.flow_count_bits)],
            "linestyle": "-" if variant.flow_count_sketch else "--",
            "linewidth": 1.4,
        }
    variants = family_plot_variants(family)[1:-1]
    index = variants.index(variant)
    return {
        "color": SERIES_COLORS[index],
        "linestyle": "-",
        "linewidth": 1.5,
    }


def ecdf_points(values: pd.Series) -> pd.DataFrame:
    sorted_values = np.sort(pd.to_numeric(values, errors="coerce").dropna())
    if len(sorted_values) != len(RUNS):
        raise RuntimeError(
            f"Expected {len(RUNS)} whole-run CDF samples, found {len(sorted_values)}"
        )
    return pd.DataFrame(
        {
            "rank": np.arange(1, len(sorted_values) + 1),
            "value": sorted_values,
            "cdf_percent": np.arange(1, len(sorted_values) + 1)
            / len(sorted_values)
            * 100,
        }
    )


def plot_family_metric(
    family: str,
    metric: str,
    metric_label: str,
    file_stem: str,
    run_metrics: pd.DataFrame,
) -> None:
    variants = family_plot_variants(family)
    figure, axes = plt.subplots(
        len(CONDITIONS),
        len(FLOW_COUNTS),
        figsize=(11.4, 6.1),
        sharey=True,
        squeeze=False,
    )
    export_rows = []

    for row_index, condition in enumerate(CONDITIONS):
        for column_index, flow_count in enumerate(FLOW_COUNTS):
            axis = axes[row_index, column_index]
            if row_index == 0:
                axis.set_title(f"{flow_count} flows")
            if column_index == 0:
                axis.set_ylabel(f"{condition.label}\nCDF of runs (%)")
            axis.set_xlabel(metric_label)

            for variant in variants:
                values = run_metrics[
                    (run_metrics["variant"] == variant.key)
                    & (run_metrics["flow_count"] == flow_count)
                    & (run_metrics["condition"] == condition.key)
                ][metric]
                points = ecdf_points(values)
                style = variant_style(variant, family)
                plot_x = np.concatenate(([points["value"].iloc[0]], points["value"]))
                plot_y = np.concatenate(([0.0], points["cdf_percent"]))
                axis.step(plot_x, plot_y, where="post", **style)
                export_rows.append(
                    points.assign(
                        family=family,
                        metric=metric,
                        variant=variant.key,
                        variant_label=variant_display_label(variant),
                        flow_count=flow_count,
                        condition=condition.key,
                        series_type="protocol",
                    )
                )

            if metric == "aggregate_goodput_mbps":
                capacity_values = run_metrics[
                    (run_metrics["variant"] == FULL_ORBCC.key)
                    & (run_metrics["flow_count"] == flow_count)
                    & (run_metrics["condition"] == condition.key)
                ]["mean_available_capacity_mbps"]
                capacity_points = ecdf_points(capacity_values)
                plot_x = np.concatenate(
                    ([capacity_points["value"].iloc[0]], capacity_points["value"])
                )
                plot_y = np.concatenate(([0.0], capacity_points["cdf_percent"]))
                axis.step(
                    plot_x,
                    plot_y,
                    where="post",
                    color=AVAILABLE_CAPACITY_COLOR,
                    linestyle="-.",
                    linewidth=1.6,
                )
                export_rows.append(
                    capacity_points.assign(
                        family=family,
                        metric="mean_available_capacity_mbps",
                        variant="available_capacity",
                        variant_label="Available capacity",
                        flow_count=flow_count,
                        condition=condition.key,
                        series_type="reference",
                    )
                )

            axis.set_ylim(0, 102)
            axis.grid(True, alpha=0.22, linewidth=0.6)

    legend_handles = []
    for variant in variants:
        style = variant_style(variant, family)
        legend_handles.append(
            Line2D([0], [0], label=variant_display_label(variant), **style)
        )
    if metric == "aggregate_goodput_mbps":
        legend_handles.append(
            Line2D(
                [0],
                [0],
                label="Available capacity",
                color=AVAILABLE_CAPACITY_COLOR,
                linestyle="-.",
                linewidth=1.6,
            )
        )

    legend_columns = 5 if family == "flow_count" else 4
    figure.legend(
        handles=legend_handles,
        loc="upper center",
        ncol=legend_columns,
        frameon=False,
        bbox_to_anchor=(0.5, 0.99),
    )
    figure.suptitle(f"{family_label(family)}: whole-run {file_stem} CDF", y=1.045)
    figure.tight_layout(rect=(0, 0, 1, 0.89))
    figure.savefig(
        PLOT_ROOT / f"{family}_{file_stem}_cdf.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)

    export_plot_dataframe(
        f"{family}_{file_stem}_cdf_points.csv",
        pd.concat(export_rows, ignore_index=True),
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            "experiment": EXPERIMENT,
            "family": family,
            "metric": metric,
            "description": (
                "Exact empirical CDF points from one whole-run average per "
                "matched 300-second trace."
            ),
            "runs": list(RUNS),
            "flow_counts": FLOW_COUNTS,
            "conditions": [condition.key for condition in CONDITIONS],
        },
    )


def ordered_run_values(
    run_metrics: pd.DataFrame,
    variant_key: str,
    flow_count: int,
    condition_key: str,
    metric: str,
) -> np.ndarray:
    rows = run_metrics[
        (run_metrics["variant"] == variant_key)
        & (run_metrics["flow_count"] == flow_count)
        & (run_metrics["condition"] == condition_key)
    ].sort_values("run")
    actual_runs = rows["run"].astype(int).tolist()
    if actual_runs != list(RUNS):
        raise RuntimeError(
            f"Expected runs {list(RUNS)} for {variant_key}/{condition_key}/"
            f"{flow_count}flows, found {actual_runs}"
        )
    return rows[metric].to_numpy(dtype=float)


def append_tradeoff_export_rows(
    export_rows: list[dict[str, object]],
    family: str,
    condition,
    flow_count: int,
    metric: str,
    series_label: str,
    variant: Variant,
    x_index: int | None,
    x_label: str,
    values: np.ndarray,
) -> None:
    mean = float(np.mean(values))
    standard_deviation = float(np.std(values))
    for run, value in zip(RUNS, values, strict=True):
        export_rows.append(
            {
                "family": family,
                "condition": condition.key,
                "flow_count": flow_count,
                "metric": metric,
                "series": series_label,
                "variant": variant.key,
                "variant_label": variant_display_label(variant),
                "x_index": x_index,
                "x_label": x_label,
                "run": run,
                "value": float(value),
                "mean": mean,
                "population_std": standard_deviation,
            }
        )


def plot_family_tradeoff(
    family: str,
    condition,
    run_metrics: pd.DataFrame,
) -> None:
    variant_series = family_variant_series(family)
    tick_labels = family_tick_labels(family)
    x_values = np.arange(len(tick_labels))
    series_styles = (
        (PINT_COLOR, "o"),
        (EXACT_COUNT_COLOR, "^"),
    )
    figure, axes = plt.subplots(
        len(TRADEOFF_METRICS),
        len(FLOW_COUNTS),
        figsize=(11.4, 7.5),
        sharex="col",
        squeeze=False,
    )
    export_rows: list[dict[str, object]] = []

    for column_index, flow_count in enumerate(FLOW_COUNTS):
        axes[0, column_index].set_title(f"{flow_count} flows")
        for row_index, (metric, metric_label) in enumerate(TRADEOFF_METRICS):
            axis = axes[row_index, column_index]
            reference_values = ordered_run_values(
                run_metrics,
                FULL_ORBCC.key,
                flow_count,
                condition.key,
                metric,
            )
            reference_mean = float(np.mean(reference_values))
            reference_std = float(np.std(reference_values))
            append_tradeoff_export_rows(
                export_rows,
                family,
                condition,
                flow_count,
                metric,
                "OrbCC full INT",
                FULL_ORBCC,
                None,
                "Reference",
                reference_values,
            )

            exact_mean = None
            for series_index, (series_label, variants) in enumerate(variant_series):
                color, marker = series_styles[series_index]
                run_matrix = np.column_stack(
                    [
                        ordered_run_values(
                            run_metrics,
                            variant.key,
                            flow_count,
                            condition.key,
                            metric,
                        )
                        for variant in variants
                    ]
                )
                for matched_values in run_matrix:
                    axis.plot(
                        x_values,
                        matched_values,
                        color=color,
                        alpha=MATCHED_RUN_ALPHA,
                        linewidth=0.65,
                        zorder=1,
                    )
                means = np.mean(run_matrix, axis=0)
                standard_deviations = np.std(run_matrix, axis=0)
                axis.errorbar(
                    x_values,
                    means,
                    yerr=standard_deviations,
                    color=color,
                    marker=marker,
                    markersize=4.5,
                    linewidth=1.5,
                    capsize=2.5,
                    label=series_label,
                    zorder=3,
                )
                exact_mean = float(means[-1])

                for x_index, variant in enumerate(variants):
                    append_tradeoff_export_rows(
                        export_rows,
                        family,
                        condition,
                        flow_count,
                        metric,
                        series_label,
                        variant,
                        x_index,
                        tick_labels[x_index].replace("\n", " "),
                        run_matrix[:, x_index],
                    )

            axis.scatter(
                [x_values[-1]],
                [exact_mean],
                color="#303030",
                marker="s",
                s=32,
                zorder=4,
            )
            axis.axhline(
                reference_mean,
                color=PROTOCOL_COLORS["orbtcp"],
                linestyle="--",
                linewidth=1.4,
                label="OrbCC (full INT)",
                zorder=2,
            )
            axis.fill_between(
                [x_values[0], x_values[-1]],
                reference_mean - reference_std,
                reference_mean + reference_std,
                color=PROTOCOL_COLORS["orbtcp"],
                alpha=0.09,
                zorder=0,
            )
            axis.set_xticks(x_values, tick_labels)
            axis.grid(True, alpha=0.22, linewidth=0.6)
            axis.set_ylim(bottom=0)
            if column_index == 0:
                axis.set_ylabel(metric_label)
            if row_index == len(TRADEOFF_METRICS) - 1:
                axis.set_xlabel(family_x_label(family))

    legend_handles = []
    for series_index, (series_label, _variants) in enumerate(variant_series):
        color, marker = series_styles[series_index]
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=color,
                marker=marker,
                linewidth=1.5,
                label=series_label,
            )
        )
    legend_handles.append(
        Line2D(
            [0],
            [0],
            color=PROTOCOL_COLORS["orbtcp"],
            linestyle="--",
            linewidth=1.4,
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
    figure.suptitle(
        f"{family_label(family)} trade-off: {condition.label}",
        y=1.02,
    )
    figure.text(
        0.5,
        0.01,
        "Mean +/- population SD; faint lines connect the same matched trace.",
        ha="center",
        fontsize=8,
        color="#555555",
    )
    figure.tight_layout(rect=(0, 0.035, 1, 0.94))
    figure.savefig(
        PLOT_ROOT / f"{family}_{condition.key}_tradeoff.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)

    export_plot_dataframe(
        f"{family}_{condition.key}_tradeoff_points.csv",
        pd.DataFrame(export_rows),
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            "experiment": EXPERIMENT,
            "family": family,
            "condition": condition.key,
            "description": (
                "Whole-run values, means, and population standard deviations "
                "used by the dynamic parameter trade-off plot. Runs are matched "
                "across every implementation."
            ),
            "runs": list(RUNS),
            "flow_counts": FLOW_COUNTS,
        },
    )


def main() -> None:
    PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    run_metrics = collect_all_runs()
    export_plot_dataframe(
        "all_run_metrics.csv",
        run_metrics,
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            "experiment": EXPERIMENT,
            "description": (
                "Whole-run metrics for 10 matched rapidly changing traces. "
                "Goodput and retransmissions are summed across flows before "
                "averaging; queueing delay is time weighted at the bottleneck."
            ),
            "simulation_time_seconds": SIMULATION_TIME_S,
            "runs": list(RUNS),
            "flow_counts": FLOW_COUNTS,
            "conditions": [condition.key for condition in CONDITIONS],
        },
    )
    for family in FAMILIES:
        for metric, metric_label, file_stem in METRICS:
            plot_family_metric(
                family, metric, metric_label, file_stem, run_metrics
            )
        for condition in CONDITIONS:
            plot_family_tradeoff(family, condition, run_metrics)


if __name__ == "__main__":
    main()
