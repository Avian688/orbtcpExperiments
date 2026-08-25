#!/usr/bin/env python3

from __future__ import annotations

from itertools import groupby
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import scienceplots

plt.style.use(["science", "no-latex"])

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experimentTuningDynamicSupport import (  # noqa: E402
    COMBINED_PINT,
    CONDITIONS,
    EXACT_PINT,
    EXPERIMENT,
    FAMILIES,
    FLOW_COUNT_EXACT_VARIANTS,
    FLOW_COUNT_SKETCH_VARIANTS,
    FLOW_COUNTS,
    FULL_ORBCC,
    MAX_BANDWIDTH_PER_FLOW_MBPS,
    MIN_BANDWIDTH_PER_FLOW_MBPS,
    MSS_BYTES,
    RUNS,
    SAMPLING_VARIANTS,
    SIMULATION_TIME_S,
    UTILIZATION_VARIANTS,
    VARIANTS,
    Variant,
    bandwidth_range_mbps,
    bottleneck_bandwidth_mbps,
    family_label,
    family_plot_variants,
    family_tick_labels,
    family_variant_series,
    family_x_label,
    trace_name,
)
from plotDataExport import export_plot_dataframe  # noqa: E402
from plotProtocolSupport import (  # noqa: E402
    FINAL_ORBCC_LABEL,
    FINAL_ORBCC_PROTOCOL,
    FULL_INT_ORBCC_PROTOCOL,
    FULL_INT_REFERENCE_LABEL,
    PROTOCOL_COLORS,
)


SIMULATIONS_DIR = SCRIPT_DIR.parents[1]
CSV_ROOT = SIMULATIONS_DIR / "paperExperiments" / EXPERIMENT / "csvs"
SCENARIO_ROOT = (
    SIMULATIONS_DIR / "paperExperiments" / "scenarios" / EXPERIMENT
)
PLOT_ROOT = SIMULATIONS_DIR / "plots" / EXPERIMENT / "cumulative"
HEATMAP_ROOT = PLOT_ROOT / "heatmaps"
PAPER_PLOT_ROOT = SIMULATIONS_DIR / "plots" / EXPERIMENT / "paperPlots"
SECONDS = pd.Index(range(SIMULATION_TIME_S), name="second")
RECOVERY_WINDOW_S = 3
T_CRITICAL_95_DF9 = 2.262

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
FINAL_ORBCC_COLOR = PROTOCOL_COLORS[FINAL_ORBCC_PROTOCOL]
FULL_INT_REFERENCE_COLOR = PROTOCOL_COLORS[FULL_INT_ORBCC_PROTOCOL]
MATCHED_RUN_ALPHA = 0.12

HIGHER_IS_BETTER_CMAP = LinearSegmentedColormap.from_list(
    "r_y_g", ["red", "yellow", "green"], N=256
)
LOWER_IS_BETTER_CMAP = LinearSegmentedColormap.from_list(
    "g_y_r", ["green", "yellow", "red"], N=256
)
PARAMETER_HEATMAP_METRICS = (
    (
        "normalized_goodput",
        "Normalized goodput",
        "goodput",
        True,
        ".3f",
    ),
    (
        "mean_queue_delay_ms",
        "Queueing delay (ms)",
        "queueing_delay",
        False,
        ".2f",
    ),
    (
        "aggregate_retransmission_mbps",
        "Retransmission rate (Mbps)",
        "retransmissions",
        False,
        ".2f",
    ),
)
LOWER_IS_BETTER_SCALE_QUANTILE = 0.90
PARAMETER_HEATMAP_GROUPS = (
    (
        "flow_count",
        "Flow-count sketch",
        (*FLOW_COUNT_SKETCH_VARIANTS, EXACT_PINT),
    ),
    (
        "utilization",
        "Utilization",
        (*UTILIZATION_VARIANTS, EXACT_PINT),
    ),
    (
        "sampling",
        "Sampling",
        (*SAMPLING_VARIANTS, EXACT_PINT),
    ),
)
PAPER_TUNING_PANELS = (
    (
        "flow_count",
        "Flow-count sketch",
        "jain_fairness",
        100.0,
        "Jain fairness difference\n(percentage points)",
    ),
    (
        "utilization",
        "Utilization encoding",
        "mean_queue_delay_ms",
        1.0,
        "Mean queueing-delay difference (ms)",
    ),
    (
        "sampling",
        "Feedback sampling",
        "mean_recovery_deficit_percent",
        1.0,
        "Post-handover goodput-deficit difference\n(percentage points)",
    ),
)
PAPER_TUNING_SIMPLE_PANELS = (
    (
        "flow_count",
        "Flow-count sketch",
        "jain_fairness",
        1.0,
        "Jain fairness",
    ),
    (
        "utilization",
        "Utilization encoding",
        "mean_queue_delay_ms",
        1.0,
        "Mean queueing delay (ms)",
    ),
    (
        "sampling",
        "Feedback sampling",
        "mean_recovery_deficit_percent",
        1.0,
        "Post-handover aggregate-goodput\ndeficit (%)",
    ),
)
PAPER_TUNING_GOODPUT_PANELS = (
    (
        "flow_count",
        "Flow-count sketch",
        "jain_fairness",
        100.0,
        "Jain fairness difference\n(percentage points)",
    ),
    (
        "utilization",
        "Utilization encoding",
        "normalized_goodput",
        100.0,
        "Normalized aggregate-goodput difference\n(percentage points)",
    ),
    (
        "sampling",
        "Feedback sampling",
        "mean_post_handover_normalized_goodput",
        100.0,
        "Post-handover aggregate-goodput difference\n(percentage points)",
    ),
)
PAPER_TUNING_GOODPUT_SIMPLE_PANELS = (
    (
        "flow_count",
        "Flow-count sketch",
        "jain_fairness",
        1.0,
        "Jain fairness",
    ),
    (
        "utilization",
        "Utilization encoding",
        "normalized_goodput",
        100.0,
        "Normalized aggregate goodput\n(% of available capacity)",
    ),
    (
        "sampling",
        "Feedback sampling",
        "mean_post_handover_normalized_goodput",
        100.0,
        "Post-handover aggregate goodput\n(% of available capacity)",
    ),
)
PAPER_VALIDATION_METRICS = (
    ("normalized_goodput", "Normalized goodput"),
    ("mean_queue_delay_ms", "Queueing delay (ms)"),
    ("retransmission_overhead_percent", "Retransmission overhead (%)"),
)


def save_standalone_legend(
    handles,
    output_path: Path,
    columns: int,
) -> None:
    columns = min(columns, len(handles))
    rows = int(np.ceil(len(handles) / columns))
    figure = plt.figure(
        figsize=(max(4.0, 2.6 * columns), max(0.55, 0.45 * rows))
    )
    figure.legend(
        handles=handles,
        loc="center",
        ncol=columns,
        frameon=False,
        columnspacing=1.5,
        handletextpad=0.6,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path,
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.02,
        transparent=True,
    )
    plt.close(figure)


def bandwidth_metadata() -> dict[str, object]:
    return {
        "bandwidth_policy": "constant fair-share range per flow",
        "bandwidth_per_flow_range_mbps": [
            MIN_BANDWIDTH_PER_FLOW_MBPS,
            MAX_BANDWIDTH_PER_FLOW_MBPS,
        ],
        "aggregate_bandwidth_ranges_mbps": {
            str(flow_count): list(bandwidth_range_mbps(flow_count))
            for flow_count in FLOW_COUNTS
        },
    }


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


def load_trace(run: int, flow_count: int) -> dict:
    path = SCENARIO_ROOT / f"{trace_name(run)}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing dynamic trace: {path}")
    trace = json.loads(path.read_text(encoding="utf-8"))
    states = []
    for source_state in trace["states"]:
        state = dict(source_state)
        state["bandwidth_mbps"] = bottleneck_bandwidth_mbps(
            flow_count, float(state["bandwidth_per_flow_mbps"])
        )
        states.append(state)
    trace["flow_count"] = flow_count
    trace["states"] = states
    return trace


def jain_fairness(values: np.ndarray) -> float:
    values = np.maximum(np.asarray(values, dtype=float), 0.0)
    denominator = len(values) * float(np.sum(np.square(values)))
    if denominator <= 0:
        return 0.0
    return float(np.square(np.sum(values)) / denominator)


def post_handover_normalized_goodput_samples(
    aggregate_goodput_bps: pd.Series,
    trace: dict,
) -> np.ndarray:
    normalized_goodput = []
    for state in trace["states"][1:]:
        # Skip the partial one-second interval containing the disconnection.
        first_full_second = int(np.ceil(float(state["reconnect_time_s"])))
        seconds = list(
            range(
                first_full_second,
                min(first_full_second + RECOVERY_WINDOW_S, SIMULATION_TIME_S),
            )
        )
        if len(seconds) != RECOVERY_WINDOW_S:
            raise RuntimeError(
                "A dynamic trace does not contain the full post-handover "
                f"recovery window at state {state['state_index']}"
            )
        goodput_mbps = (
            aggregate_goodput_bps.reindex(seconds).to_numpy(dtype=float)
            / 1_000_000
        )
        if not np.all(np.isfinite(goodput_mbps)):
            raise RuntimeError(
                "Missing aggregate goodput samples in the post-handover "
                f"recovery window at state {state['state_index']}"
            )
        capacity_mbps = float(state["bandwidth_mbps"])
        if capacity_mbps <= 0:
            raise RuntimeError(
                "Non-positive bottleneck capacity in the post-handover "
                f"recovery window at state {state['state_index']}"
            )
        normalized_goodput.extend(goodput_mbps / capacity_mbps)
    if not normalized_goodput:
        raise RuntimeError("Dynamic trace contains no handovers to evaluate")
    return np.asarray(normalized_goodput, dtype=float)


def mean_recovery_deficit_percent(
    aggregate_goodput_bps: pd.Series,
    trace: dict,
) -> float:
    normalized_goodput = post_handover_normalized_goodput_samples(
        aggregate_goodput_bps,
        trace,
    )
    deficits = np.clip(1.0 - normalized_goodput, 0.0, 1.0) * 100.0
    return float(np.mean(deficits))


def mean_post_handover_normalized_goodput(
    aggregate_goodput_bps: pd.Series,
    trace: dict,
) -> float:
    return float(
        np.mean(
            post_handover_normalized_goodput_samples(
                aggregate_goodput_bps,
                trace,
            )
        )
    )


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
    minimum_bandwidth_mbps, maximum_bandwidth_mbps = bandwidth_range_mbps(
        flow_count
    )
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

    goodput_frame = pd.concat(goodput_series, axis=1)
    retransmission_frame = pd.concat(retransmission_series, axis=1)
    aggregate_goodput_bps = goodput_frame.sum(axis=1)
    aggregate_retransmission_bps = retransmission_frame.sum(axis=1)
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
    trace = load_trace(run, flow_count)
    mean_queue_delay_ms, mean_available_capacity_mbps = path_and_queue_means(
        queue_frame, trace
    )
    mean_goodput_bps = float(aggregate_goodput_bps.mean())
    mean_retransmission_bps = float(aggregate_retransmission_bps.mean())
    if mean_goodput_bps <= 0:
        raise RuntimeError(
            f"Non-positive aggregate goodput for {variant.key}/"
            f"{condition.key}/{flow_count}flows/run{run}"
        )
    aggregate_goodput_mbps = mean_goodput_bps / 1_000_000
    aggregate_retransmission_mbps = mean_retransmission_bps / 1_000_000

    return {
        "variant": variant.key,
        "variant_label": variant.label,
        "family": variant.family,
        "flow_count": flow_count,
        "bandwidth_per_flow_min_mbps": MIN_BANDWIDTH_PER_FLOW_MBPS,
        "bandwidth_per_flow_max_mbps": MAX_BANDWIDTH_PER_FLOW_MBPS,
        "bottleneck_bandwidth_min_mbps": minimum_bandwidth_mbps,
        "bottleneck_bandwidth_max_mbps": maximum_bandwidth_mbps,
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
        "jain_fairness": jain_fairness(
            goodput_frame.mean(axis=0).to_numpy(dtype=float)
        ),
        "mean_queue_delay_ms": mean_queue_delay_ms,
        "mean_recovery_deficit_percent": mean_recovery_deficit_percent(
            aggregate_goodput_bps,
            trace,
        ),
        "mean_post_handover_normalized_goodput": (
            mean_post_handover_normalized_goodput(
                aggregate_goodput_bps,
                trace,
            )
        ),
        "aggregate_retransmission_mbps": aggregate_retransmission_mbps,
        "retransmission_overhead_percent": (
            mean_retransmission_bps / mean_goodput_bps * 100.0
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
        return FULL_INT_REFERENCE_LABEL
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
            "color": FULL_INT_REFERENCE_COLOR,
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
            **bandwidth_metadata(),
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
                FULL_INT_REFERENCE_LABEL,
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
                color=FULL_INT_REFERENCE_COLOR,
                linestyle="--",
                linewidth=1.4,
                label=FULL_INT_REFERENCE_LABEL,
                zorder=2,
            )
            axis.fill_between(
                [x_values[0], x_values[-1]],
                reference_mean - reference_std,
                reference_mean + reference_std,
                color=FULL_INT_REFERENCE_COLOR,
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
            color=FULL_INT_REFERENCE_COLOR,
            linestyle="--",
            linewidth=1.4,
            label=FULL_INT_REFERENCE_LABEL,
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
            **bandwidth_metadata(),
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


def parameter_heatmap_label(family: str, variant: Variant) -> str:
    if family == "flow_count":
        if variant == EXACT_PINT:
            return "Exact (16-bit)"
        return f"{variant.flow_count_bits}-bit sketch"
    if family == "utilization":
        if variant == EXACT_PINT:
            return "Exact"
        return f"{variant.utilization_bits} bits"
    if family == "sampling":
        if variant == EXACT_PINT:
            return "p=1 (exact)"
        return variant.label
    raise ValueError(f"Unknown tuning family: {family}")


def parameter_heatmap_row_definitions() -> list[dict[str, object]]:
    rows = []
    for family, group_label, variants in PARAMETER_HEATMAP_GROUPS:
        for variant in variants:
            parameter_label = parameter_heatmap_label(family, variant)
            rows.append(
                {
                    "row_index": len(rows),
                    "family": family,
                    "group_label": group_label,
                    "parameter_label": parameter_label,
                    "row_label": f"{group_label}: {parameter_label}",
                    "variant": variant,
                }
            )
    return rows


def parameter_decision_heatmap_rows(
    run_metrics: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    row_definitions = parameter_heatmap_row_definitions()
    columns = [
        (condition, flow_count)
        for condition in CONDITIONS
        for flow_count in FLOW_COUNTS
    ]

    for row_definition in row_definitions:
        variant = row_definition["variant"]
        for column_index, (condition, flow_count) in enumerate(columns):
            for (
                metric,
                metric_label,
                file_stem,
                higher_is_better,
                _value_format,
            ) in PARAMETER_HEATMAP_METRICS:
                values = ordered_run_values(
                    run_metrics,
                    variant.key,
                    flow_count,
                    condition.key,
                    metric,
                )
                rows.append(
                    {
                        "row_index": row_definition["row_index"],
                        "column_index": column_index,
                        "family": row_definition["family"],
                        "group_label": row_definition["group_label"],
                        "parameter_label": row_definition["parameter_label"],
                        "row_label": row_definition["row_label"],
                        "variant": variant.key,
                        "condition": condition.key,
                        "condition_label": condition.label,
                        "flow_count": flow_count,
                        "metric": metric,
                        "metric_label": metric_label,
                        "file_stem": file_stem,
                        "higher_is_better": higher_is_better,
                        "mean": float(np.mean(values)),
                        "population_std": float(np.std(values)),
                    }
                )
    return pd.DataFrame(rows)


def nice_upper_bound(value: float) -> float:
    if not np.isfinite(value) or value <= 0:
        return 1.0
    magnitude = 10 ** np.floor(np.log10(value))
    scaled = value / magnitude
    if scaled <= 1:
        factor = 1
    elif scaled <= 2:
        factor = 2
    elif scaled <= 5:
        factor = 5
    else:
        factor = 10
    return float(factor * magnitude)


def parameter_heatmap_scales(
    heatmap_rows: pd.DataFrame,
) -> dict[str, tuple[float, float]]:
    scales = {"normalized_goodput": (0.8, 1.0)}
    for metric, _label, _stem, higher_is_better, _format in (
        PARAMETER_HEATMAP_METRICS
    ):
        if higher_is_better:
            continue
        values = heatmap_rows.loc[heatmap_rows["metric"] == metric, "mean"]
        values = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
        if values.size == 0:
            raise RuntimeError(f"No values available to scale {metric}")
        upper = float(np.quantile(values, LOWER_IS_BETTER_SCALE_QUANTILE))
        if upper <= 0:
            upper = float(np.max(values))
        scales[metric] = (0.0, nice_upper_bound(upper))
    return scales


def plot_parameter_heatmap(
    family: str,
    group_label: str,
    metric: str,
    metric_label: str,
    file_stem: str,
    higher_is_better: bool,
    value_format: str,
    heatmap_rows: pd.DataFrame,
    color_limits: tuple[float, float],
) -> None:
    row_definitions = [
        row
        for row in parameter_heatmap_row_definitions()
        if row["family"] == family
    ]
    columns = [
        (condition, flow_count)
        for condition in CONDITIONS
        for flow_count in FLOW_COUNTS
    ]
    column_labels = [
        f"{condition.label}\n{flow_count} flows"
        for condition, flow_count in columns
    ]
    row_labels = [row["parameter_label"] for row in row_definitions]
    means = np.full((len(row_definitions), len(columns)), np.nan)
    standard_deviations = np.full_like(means, np.nan)

    metric_rows = heatmap_rows[
        (heatmap_rows["family"] == family)
        & (heatmap_rows["metric"] == metric)
    ]
    for local_row_index, row_definition in enumerate(row_definitions):
        for column_index in range(len(columns)):
            cell = metric_rows[
                (metric_rows["variant"] == row_definition["variant"].key)
                & (metric_rows["column_index"] == column_index)
            ]
            if len(cell) != 1:
                raise RuntimeError(
                    "Expected one dynamic heatmap cell for "
                    f"{family}/{metric}/row{local_row_index}/column{column_index}, "
                    f"found {len(cell)}"
                )
            means[local_row_index, column_index] = float(cell.iloc[0]["mean"])
            standard_deviations[local_row_index, column_index] = float(
                cell.iloc[0]["population_std"]
            )

    if not np.all(np.isfinite(means)):
        raise RuntimeError(f"Incomplete parameter heatmap for {family}/{metric}")

    color_minimum, color_maximum = color_limits
    color_map = (
        HIGHER_IS_BETTER_CMAP if higher_is_better else LOWER_IS_BETTER_CMAP
    )
    color_norm = Normalize(
        vmin=color_minimum,
        vmax=color_maximum,
        clip=True,
    )
    figure, axis = plt.subplots(figsize=(10.2, 4.8))
    image = axis.imshow(
        means,
        origin="upper",
        aspect="auto",
        interpolation="nearest",
        cmap=color_map,
        norm=color_norm,
    )

    axis.set_xticks(range(len(columns)), column_labels)
    axis.set_yticks(range(len(row_definitions)), row_labels)
    axis.set_xlabel("Dynamic condition and concurrent flows")
    axis.set_ylabel(group_label)
    axis.axvline(len(FLOW_COUNTS) - 0.5, color="white", linewidth=2.0)

    for row_index in range(len(row_definitions)):
        for column_index in range(len(columns)):
            axis.text(
                column_index,
                row_index,
                (
                    f"{means[row_index, column_index]:{value_format}}"
                    "+/-"
                    f"{standard_deviations[row_index, column_index]:{value_format}}"
                ),
                ha="center",
                va="center",
                color="black",
                fontsize=8,
            )

    axis.set_title(f"{group_label}: {metric_label}")
    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.set_label(metric_label)
    colorbar.set_ticks(np.linspace(color_minimum, color_maximum, num=3))
    figure.text(
        0.5,
        0.015,
        (
            "Cells show 10-run mean +/- population SD. Values outside the "
            "shared metric colour range are clipped to the end colour."
        ),
        ha="center",
        fontsize=8,
        color="#555555",
    )
    figure.tight_layout(rect=(0, 0.055, 1, 1))
    HEATMAP_ROOT.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        HEATMAP_ROOT / f"{family}_{file_stem}_heatmap.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)

    export_rows = metric_rows.copy()
    export_rows["color_vmin"] = color_minimum
    export_rows["color_vmax"] = color_maximum
    export_rows["color_direction"] = (
        "higher_is_better" if higher_is_better else "lower_is_better"
    )
    export_plot_dataframe(
        f"{family}_{file_stem}_heatmap_points.csv",
        export_rows,
        base_dir=PLOT_ROOT / "plot_data" / "heatmaps",
        metadata={
            **bandwidth_metadata(),
            "experiment": EXPERIMENT,
            "family": family,
            "metric": metric,
            "description": (
                "Final raw means and population standard deviations for one "
                "dynamic parameter-decision heatmap. All feature heatmaps for "
                "this metric use the same colour limits."
            ),
            "runs": list(RUNS),
            "flow_counts": FLOW_COUNTS,
            "conditions": [condition.key for condition in CONDITIONS],
            "color_vmin": color_minimum,
            "color_vmax": color_maximum,
            "color_direction": (
                "higher_is_better"
                if higher_is_better
                else "lower_is_better"
            ),
            "lower_is_better_scale_quantile": (
                LOWER_IS_BETTER_SCALE_QUANTILE
                if not higher_is_better
                else None
            ),
        },
    )


def plot_parameter_decision_heatmaps(run_metrics: pd.DataFrame) -> None:
    heatmap_rows = parameter_decision_heatmap_rows(run_metrics)
    color_scales = parameter_heatmap_scales(heatmap_rows)

    obsolete_outputs = (
        PLOT_ROOT / "parameter_decision_heatmaps.pdf",
        PLOT_ROOT / "plot_data" / "parameter_decision_heatmaps_points.csv",
        PLOT_ROOT
        / "plot_data"
        / "parameter_decision_heatmaps_points.csv.metadata.json",
    )
    for obsolete_output in obsolete_outputs:
        obsolete_output.unlink(missing_ok=True)

    for family, group_label, _variants in PARAMETER_HEATMAP_GROUPS:
        for (
            metric,
            metric_label,
            file_stem,
            higher_is_better,
            value_format,
        ) in PARAMETER_HEATMAP_METRICS:
            plot_parameter_heatmap(
                family,
                group_label,
                metric,
                metric_label,
                file_stem,
                higher_is_better,
                value_format,
                heatmap_rows,
                color_scales[metric],
            )


def confidence_summary(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    if len(values) != len(RUNS) or not np.all(np.isfinite(values)):
        raise RuntimeError(
            f"Expected {len(RUNS)} finite trace-level values, found {len(values)}"
        )
    mean = float(np.mean(values))
    sample_std = float(np.std(values, ddof=1))
    margin = T_CRITICAL_95_DF9 * sample_std / np.sqrt(len(values))
    return {
        "mean": mean,
        "population_std": float(np.std(values)),
        "sample_std": sample_std,
        "ci95_lower": mean - margin,
        "ci95_upper": mean + margin,
        "ci95_margin": margin,
    }


def paired_metric_deltas(
    run_metrics: pd.DataFrame,
    variant: Variant,
    metric: str,
    scale: float,
) -> pd.DataFrame:
    keys = ["flow_count", "condition", "run"]
    candidate = run_metrics[run_metrics["variant"] == variant.key][
        [*keys, metric]
    ].rename(columns={metric: "candidate_value"})
    exact = run_metrics[run_metrics["variant"] == EXACT_PINT.key][
        [*keys, metric]
    ].rename(columns={metric: "exact_value"})
    paired = candidate.merge(exact, on=keys, how="inner", validate="one_to_one")
    expected_rows = len(FLOW_COUNTS) * len(CONDITIONS) * len(RUNS)
    if len(paired) != expected_rows:
        raise RuntimeError(
            f"Expected {expected_rows} paired values for {variant.key}/{metric}, "
            f"found {len(paired)}"
        )
    paired["delta"] = (
        paired["candidate_value"] - paired["exact_value"]
    ) * scale
    return paired


def selected_parameter_variant(family: str) -> Variant:
    if family == "flow_count":
        candidates = FLOW_COUNT_SKETCH_VARIANTS
        selected_value = COMBINED_PINT.flow_count_bits
        attribute = "flow_count_bits"
    elif family == "utilization":
        candidates = UTILIZATION_VARIANTS
        selected_value = COMBINED_PINT.utilization_bits
        attribute = "utilization_bits"
    elif family == "sampling":
        candidates = (*SAMPLING_VARIANTS, EXACT_PINT)
        selected_value = COMBINED_PINT.feedback_probability
        attribute = "feedback_probability"
    else:
        raise ValueError(f"Unknown tuning family: {family}")

    matches = [
        variant
        for variant in candidates
        if np.isclose(float(getattr(variant, attribute)), float(selected_value))
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one selected {family} variant for {selected_value}, "
            f"found {len(matches)}"
        )
    return matches[0]


def tuning_panel_rows(
    run_metrics: pd.DataFrame,
    family: str,
    metric: str,
    scale: float,
) -> pd.DataFrame:
    variants = next(
        variants
        for group_family, _label, variants in PARAMETER_HEATMAP_GROUPS
        if group_family == family
    )
    selected_variant = selected_parameter_variant(family)
    rows = []

    for x_index, variant in enumerate(variants):
        paired = paired_metric_deltas(run_metrics, variant, metric, scale)
        trace_values = (
            paired.groupby("run", sort=True)["delta"]
            .mean()
            .reindex(RUNS)
            .to_numpy(dtype=float)
        )
        summary = confidence_summary(trace_values)
        rows.append(
            {
                "family": family,
                "metric": metric,
                "variant": variant.key,
                "variant_label": parameter_heatmap_label(family, variant),
                "x_index": x_index,
                "selected": variant == selected_variant,
                **summary,
                "trace_values": trace_values.tolist(),
            }
        )
    return pd.DataFrame(rows)


def direct_tuning_panel_rows(
    run_metrics: pd.DataFrame,
    family: str,
    metric: str,
    scale: float,
) -> pd.DataFrame:
    variants = next(
        variants
        for group_family, _label, variants in PARAMETER_HEATMAP_GROUPS
        if group_family == family
    )
    selected_variant = selected_parameter_variant(family)
    expected_rows = len(FLOW_COUNTS) * len(CONDITIONS) * len(RUNS)
    rows = []

    for x_index, variant in enumerate(variants):
        values = run_metrics[run_metrics["variant"] == variant.key][
            ["flow_count", "condition", "run", metric]
        ].copy()
        if len(values) != expected_rows:
            raise RuntimeError(
                f"Expected {expected_rows} direct values for "
                f"{variant.key}/{metric}, found {len(values)}"
            )
        values["plot_value"] = values[metric] * scale
        trace_values = (
            values.groupby("run", sort=True)["plot_value"]
            .mean()
            .reindex(RUNS)
            .to_numpy(dtype=float)
        )
        summary = confidence_summary(trace_values)
        rows.append(
            {
                "family": family,
                "metric": metric,
                "variant": variant.key,
                "variant_label": parameter_heatmap_label(family, variant),
                "x_index": x_index,
                "selected": variant == selected_variant,
                **summary,
                "trace_values": trace_values.tolist(),
            }
        )
    return pd.DataFrame(rows)


def plot_tuning_decision_figure(
    run_metrics: pd.DataFrame,
    panels,
    panel_rows_function,
    output_stem: str,
    mean_legend_label: str,
    description: str,
    draw_zero_reference: bool,
) -> None:
    figure, axes = plt.subplots(1, len(panels), figsize=(12, 4.1))
    export_rows = []
    primary_color = FINAL_ORBCC_COLOR

    for axis, (
        family,
        title,
        metric,
        scale,
        y_label,
    ) in zip(axes, panels, strict=True):
        panel_rows = panel_rows_function(
            run_metrics,
            family,
            metric,
            scale,
        )
        export_rows.append(panel_rows)
        x_values = panel_rows["x_index"].to_numpy(dtype=float)
        means = panel_rows["mean"].to_numpy(dtype=float)
        margins = panel_rows["ci95_margin"].to_numpy(dtype=float)

        selected_index = int(
            panel_rows.loc[panel_rows["selected"], "x_index"].iloc[0]
        )
        axis.axvspan(
            selected_index - 0.24,
            selected_index + 0.24,
            color=primary_color,
            alpha=0.10,
            zorder=0,
        )
        axis.errorbar(
            x_values,
            means,
            yerr=margins,
            color=primary_color,
            marker="o",
            markersize=5,
            linewidth=1.6,
            capsize=3,
            zorder=3,
        )
        selected_mean = float(
            panel_rows.loc[panel_rows["selected"], "mean"].iloc[0]
        )
        axis.scatter(
            [selected_index],
            [selected_mean],
            color=primary_color,
            edgecolor="black",
            marker="*",
            s=115,
            linewidth=0.7,
            zorder=5,
        )
        if draw_zero_reference:
            axis.axhline(0, color="#555555", linestyle="--", linewidth=1.0)
        axis.set_xticks(
            x_values,
            panel_rows["variant_label"].str.replace(" ", "\n", n=1),
        )
        axis.set_title(title)
        axis.set_ylabel(y_label)
        axis.set_xlabel(family_x_label(family))
        axis.grid(True, axis="y", alpha=0.25, linewidth=0.6)

    legend_handles = (
        Line2D(
            [0],
            [0],
            color=FINAL_ORBCC_COLOR,
            marker="o",
            linewidth=1.6,
            label=mean_legend_label,
        ),
        Line2D(
            [0],
            [0],
            color=FINAL_ORBCC_COLOR,
            marker="*",
            markeredgecolor="black",
            linestyle="none",
            markersize=10,
            label="Selected value",
        ),
    )
    PAPER_PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    save_standalone_legend(
        legend_handles,
        PAPER_PLOT_ROOT / f"{output_stem}_legend.pdf",
        2,
    )
    figure.tight_layout()
    figure.savefig(
        PAPER_PLOT_ROOT / f"{output_stem}.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)

    export_plot_dataframe(
        f"{output_stem}_points.csv",
        pd.concat(export_rows, ignore_index=True),
        base_dir=PAPER_PLOT_ROOT / "plot_data",
        metadata={
            **bandwidth_metadata(),
            "experiment": EXPERIMENT,
            "description": description,
            "runs": list(RUNS),
            "flow_counts": FLOW_COUNTS,
            "conditions": [condition.key for condition in CONDITIONS],
            "recovery_window_seconds": RECOVERY_WINDOW_S,
            "combined_configuration": COMBINED_PINT.label,
        },
    )


def plot_paper_tuning_decisions(run_metrics: pd.DataFrame) -> None:
    plot_tuning_decision_figure(
        run_metrics=run_metrics,
        panels=PAPER_TUNING_PANELS,
        panel_rows_function=tuning_panel_rows,
        output_stem="tuning_decisions",
        mean_legend_label="Mean difference from Exact PINT (95% CI)",
        description=(
            "Final paired differences for the three-panel parameter-selection "
            "figure. Each confidence interval treats a matched dynamic trace as "
            "the independent unit after averaging its six workloads."
        ),
        draw_zero_reference=True,
    )


def plot_paper_tuning_decisions_simple(run_metrics: pd.DataFrame) -> None:
    plot_tuning_decision_figure(
        run_metrics=run_metrics,
        panels=PAPER_TUNING_SIMPLE_PANELS,
        panel_rows_function=direct_tuning_panel_rows,
        output_stem="tuning_decisions_simple",
        mean_legend_label="Mean value (95% CI)",
        description=(
            "Final direct values for the simpler three-panel parameter-selection "
            "figure. Each confidence interval treats a matched dynamic trace as "
            "the independent unit after averaging its six workloads."
        ),
        draw_zero_reference=False,
    )


def plot_paper_tuning_decisions_goodput(run_metrics: pd.DataFrame) -> None:
    plot_tuning_decision_figure(
        run_metrics=run_metrics,
        panels=PAPER_TUNING_GOODPUT_PANELS,
        panel_rows_function=tuning_panel_rows,
        output_stem="tuning_decisions_goodput",
        mean_legend_label="Mean difference from Exact PINT (95% CI)",
        description=(
            "Final paired differences for the goodput-focused parameter-selection "
            "figure. Aggregate goodput is normalized by contemporaneous "
            "bottleneck capacity before workloads are combined."
        ),
        draw_zero_reference=True,
    )


def plot_paper_tuning_decisions_goodput_simple(
    run_metrics: pd.DataFrame,
) -> None:
    plot_tuning_decision_figure(
        run_metrics=run_metrics,
        panels=PAPER_TUNING_GOODPUT_SIMPLE_PANELS,
        panel_rows_function=direct_tuning_panel_rows,
        output_stem="tuning_decisions_goodput_simple",
        mean_legend_label="Mean value (95% CI)",
        description=(
            "Final direct values for the goodput-focused parameter-selection "
            "figure. Aggregate goodput is normalized by contemporaneous "
            "bottleneck capacity before workloads are combined."
        ),
        draw_zero_reference=False,
    )


def validation_variant_styles() -> tuple[
    tuple[Variant, str, str, str, str], ...
]:
    return (
        (
            COMBINED_PINT,
            FINAL_ORBCC_LABEL,
            FINAL_ORBCC_COLOR,
            "o",
            "-",
        ),
        (EXACT_PINT, "Exact PINT", "#303030", "s", "--"),
        (
            FULL_ORBCC,
            FULL_INT_REFERENCE_LABEL,
            FULL_INT_REFERENCE_COLOR,
            "^",
            ":",
        ),
    )


def plot_paper_combined_validation(run_metrics: pd.DataFrame) -> None:
    columns = [
        (condition, flow_count)
        for condition in CONDITIONS
        for flow_count in FLOW_COUNTS
    ]
    column_labels = [
        f"{condition.label}\n{flow_count} flows"
        for condition, flow_count in columns
    ]
    figure, axes = plt.subplots(
        len(PAPER_VALIDATION_METRICS),
        1,
        figsize=(10.2, 8.2),
        sharex=True,
    )
    export_rows = []
    offsets = (-0.12, 0.0, 0.12)

    for axis, (metric, metric_label) in zip(
        axes, PAPER_VALIDATION_METRICS, strict=True
    ):
        for style_index, (
            variant,
            variant_label,
            color,
            marker,
            linestyle,
        ) in enumerate(validation_variant_styles()):
            means = []
            margins = []
            for column_index, (condition, flow_count) in enumerate(columns):
                values = ordered_run_values(
                    run_metrics,
                    variant.key,
                    flow_count,
                    condition.key,
                    metric,
                )
                summary = confidence_summary(values)
                means.append(summary["mean"])
                margins.append(summary["ci95_margin"])
                export_rows.append(
                    {
                        "metric": metric,
                        "metric_label": metric_label,
                        "variant": variant.key,
                        "variant_label": variant_label,
                        "column_index": column_index,
                        "condition": condition.key,
                        "flow_count": flow_count,
                        **summary,
                        "run_values": values.tolist(),
                    }
                )

            means = np.asarray(means)
            margins = np.asarray(margins)
            shifted_x = np.arange(len(columns), dtype=float) + offsets[style_index]
            condition_slices = (
                (0, len(FLOW_COUNTS)),
                (len(FLOW_COUNTS), len(columns)),
            )
            for start, end in condition_slices:
                axis.errorbar(
                    shifted_x[start:end],
                    means[start:end],
                    yerr=margins[start:end],
                    color=color,
                    marker=marker,
                    linestyle=linestyle,
                    linewidth=1.5,
                    markersize=4.5,
                    capsize=2.5,
                    label=variant_label if start == 0 else None,
                )

        axis.axvline(len(FLOW_COUNTS) - 0.5, color="#888888", linewidth=1.0)
        axis.set_ylabel(metric_label)
        axis.set_ylim(bottom=0)
        axis.grid(True, axis="y", alpha=0.25, linewidth=0.6)

    axes[-1].set_xticks(range(len(columns)), column_labels)
    axes[-1].set_xlabel("Dynamic condition and concurrent flows")
    legend_handles, _ = axes[0].get_legend_handles_labels()
    PAPER_PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    save_standalone_legend(
        legend_handles,
        PAPER_PLOT_ROOT / "combined_validation_legend.pdf",
        3,
    )
    figure.text(
        0.5,
        0.01,
        "Points show ten-run means with 95% confidence intervals.",
        ha="center",
        fontsize=8,
        color="#555555",
    )
    figure.tight_layout(rect=(0, 0.035, 1, 1))
    figure.savefig(
        PAPER_PLOT_ROOT / "combined_validation.pdf",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(figure)

    export_plot_dataframe(
        "combined_validation_points.csv",
        pd.DataFrame(export_rows),
        base_dir=PAPER_PLOT_ROOT / "plot_data",
        metadata={
            **bandwidth_metadata(),
            "experiment": EXPERIMENT,
            "description": (
                "Final points for the combined OrbCC validation figure. "
                "Confidence intervals are calculated across ten matched traces."
            ),
            "runs": list(RUNS),
            "flow_counts": FLOW_COUNTS,
            "conditions": [condition.key for condition in CONDITIONS],
            "combined_configuration": COMBINED_PINT.label,
        },
    )


def plot_paper_figures(run_metrics: pd.DataFrame) -> None:
    plot_paper_tuning_decisions(run_metrics)
    plot_paper_tuning_decisions_simple(run_metrics)
    plot_paper_tuning_decisions_goodput(run_metrics)
    plot_paper_tuning_decisions_goodput_simple(run_metrics)
    plot_paper_combined_validation(run_metrics)


def main() -> None:
    PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    run_metrics = collect_all_runs()
    export_plot_dataframe(
        "all_run_metrics.csv",
        run_metrics,
        base_dir=PLOT_ROOT / "plot_data",
        metadata={
            **bandwidth_metadata(),
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
    plot_parameter_decision_heatmaps(run_metrics)
    plot_paper_figures(run_metrics)


if __name__ == "__main__":
    main()
