#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, NullLocator
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experimentSensitivityAnalysisSupport import (  # noqa: E402
    DISTRIBUTED_NO_LOSS,
    EXACT_PINT,
    EXPERIMENT,
    FEEDBACK_VARIANTS,
    FINAL_ORBCC,
    HANDOVER_VARIANTS,
    RUNS,
    SIMULATION_TIME_S,
    VALIDATION_VARIANTS,
    cases,
    feedback_analysis_cases,
    handover_cases,
    trace_name,
    validation_cases,
)
from plotDataExport import export_plot_dataframe  # noqa: E402
from plotProtocolSupport import PROTOCOL_COLORS  # noqa: E402


SIMULATIONS_DIR = SCRIPT_DIR.parents[1]
PAPER_EXPERIMENT_DIR = SIMULATIONS_DIR / "paperExperiments" / EXPERIMENT
CSV_ROOT = PAPER_EXPERIMENT_DIR / "csvs"
SYNTHETIC_ROOT = PAPER_EXPERIMENT_DIR / "synthetic"
SCENARIO_ROOT = SIMULATIONS_DIR / "paperExperiments" / "scenarios" / EXPERIMENT
PLOT_ROOT = SIMULATIONS_DIR / "plots" / EXPERIMENT
PAPER_PLOT_ROOT = PLOT_ROOT / "paperPlots"
PLOT_DATA_ROOT = PAPER_PLOT_ROOT / "plot_data"

FONT_SIZE = 10
LEGEND_FONT_SIZE = 8
# Experiment 4/5 aggregate plots use a 4.5 x 1.2 inch half-page canvas.
# Three sensitivity panels therefore use one third of the page each while
# retaining the same plot height.
PANEL_FIGSIZE = (3.0, 1.2)
COMBINED_FIGSIZE = (9.0, 1.2)
TOP_LEGEND_Y = 1.2
EVENT_BIN_RTTS = 0.5
EVENT_WINDOW_RTTS = 10.0

VARIANT_COLORS = {
    "exact": "#303030",
    "lc_only": "#0C5DA5",
    "flow_encoding_only": "#00A087",
    "utilization_encoding_only": "#D1495B",
    "lc_flow_encoding": "#7E2F8E",
    "orbcc": PROTOCOL_COLORS["orbtcp_pint"],
}
VARIANT_MARKERS = {
    "exact": "s",
    "lc_only": "o",
    "flow_encoding_only": "^",
    "utilization_encoding_only": "D",
    "lc_flow_encoding": "v",
    "orbcc": "o",
}
COMPACT_VARIANT_LABELS = {
    "exact": "Exact PINT",
    "lc_only": "Linear Counting",
    "flow_encoding_only": "N/S encoding",
    "utilization_encoding_only": "U encoding",
    "lc_flow_encoding": "LC + N/S encoding",
    "orbcc": "OrbCC",
}


plt.rcParams.update(
    {
        "font.family": "DejaVu Serif",
        "font.size": FONT_SIZE,
        "axes.labelsize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": LEGEND_FONT_SIZE,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def case_root(case) -> Path:
    return (
        CSV_ROOT
        / case.workload.experiment_key
        / case.variant.key
        / case.condition.key
        / case.workload.key
        / f"run{case.run}"
    )


def read_vector(path: Path, metric: str) -> pd.DataFrame:
    frame = pd.read_csv(path, usecols=["time", metric])
    frame["time"] = pd.to_numeric(frame["time"], errors="coerce")
    frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    return frame.dropna().sort_values("time")


def metric_files(case, metric: str) -> list[Path]:
    root = case_root(case)
    if not root.is_dir():
        raise FileNotFoundError(f"Missing extracted case directory: {root}")
    paths = sorted(root.rglob(f"{metric}.csv"))
    if not paths:
        raise FileNotFoundError(f"Missing {metric} vectors below {root}")
    return paths


def endpoint_index(path: Path, endpoint: str) -> int | None:
    match = re.search(rf"{endpoint}\[(\d+)]", path.parent.name)
    return int(match.group(1)) if match else None


def load_per_flow_metric(case, metric: str) -> pd.DataFrame:
    endpoint = "server" if metric == "goodput" else "client"
    series = []
    for path in metric_files(case, metric):
        index = endpoint_index(path, endpoint)
        if index is None:
            continue
        frame = read_vector(path, metric)
        values = frame.groupby("time", sort=True)[metric].mean()
        values.name = index
        series.append(values)
    if not series:
        raise RuntimeError(
            f"No {endpoint} {metric} vectors for {case.config_name}"
        )
    # Keep gaps from vector(removeRepeats) distinct from genuine zero values.
    # Callers can then restore the held value or resample the periodic signal.
    return pd.concat(series, axis=1).sort_index()


def restore_remove_repeats(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.ffill().fillna(0.0)


def is_bottleneck_queue(path: Path) -> bool:
    module = path.parent.name
    return bool(re.search(r"\.transit[AB]\.ppp\[1]\.queue$", module))


def load_queue_metric(case, metric: str) -> pd.DataFrame:
    frames = []
    for path in metric_files(case, metric):
        if not is_bottleneck_queue(path):
            continue
        frame = read_vector(path, metric)
        frame["module"] = path.parent.name
        frames.append(frame)
    if not frames:
        raise RuntimeError(
            f"No transit bottleneck {metric} vectors for {case.config_name}"
        )
    return pd.concat(frames, ignore_index=True).sort_values("time")


def load_utilization_error(case) -> pd.DataFrame:
    root = case_root(case)
    local_paths = {
        path.parent.name: path
        for path in root.rglob("pintLocalUtilization.csv")
        if is_bottleneck_queue(path)
    }
    decoded_paths = {
        path.parent.name: path
        for path in root.rglob("pintDecodedUtilization.csv")
        if is_bottleneck_queue(path)
    }
    frames = []
    for module in sorted(local_paths.keys() & decoded_paths.keys()):
        local = read_vector(local_paths[module], "pintLocalUtilization")
        decoded = read_vector(
            decoded_paths[module], "pintDecodedUtilization"
        )
        local["occurrence"] = local.groupby("time").cumcount()
        decoded["occurrence"] = decoded.groupby("time").cumcount()
        merged = pd.merge(
            local,
            decoded,
            on=["time", "occurrence"],
            how="inner",
            validate="one_to_one",
        )
        merged = merged[merged.pintLocalUtilization > 0].copy()
        merged["u_absolute_relative_error_percent"] = (
            (
                merged.pintDecodedUtilization
                - merged.pintLocalUtilization
            ).abs()
            / merged.pintLocalUtilization
            * 100
        )
        merged["module"] = module
        frames.append(merged)
    if not frames:
        raise RuntimeError(
            f"Unable to pair U telemetry for {case.config_name}"
        )
    return pd.concat(frames, ignore_index=True).sort_values("time")


def load_trace(run: int) -> dict:
    path = SCENARIO_ROOT / f"{trace_name(run)}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing sensitivity trace: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def confidence_multiplier(sample_count: int) -> float:
    return {5: 2.776, 10: 2.262}.get(sample_count, 1.96)


def summarize(
    frame: pd.DataFrame, groups: list[str], value: str
) -> pd.DataFrame:
    summary = (
        frame.groupby(groups)[value]
        .agg(mean="mean", std="std", count="count")
        .reset_index()
    )
    summary["ci95"] = summary.apply(
        lambda row: (
            confidence_multiplier(int(row["count"]))
            * float(row["std"])
            / math.sqrt(int(row["count"]))
            if row["count"] > 1
            else 0.0
        ),
        axis=1,
    )
    return summary


def save_figure(figure, filename: str) -> None:
    PAPER_PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    path = PAPER_PLOT_ROOT / filename
    figure.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(figure)
    print(f"Saved {path}")


def add_top_axis_legend(axis, handles=None, labels=None, *, columns: int) -> None:
    if handles is None or labels is None:
        handles, labels = axis.get_legend_handles_labels()
    rows = math.ceil(len(labels) / columns)
    anchor_y = TOP_LEGEND_Y + 0.14 * (rows - 1)
    axis.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, anchor_y),
        ncol=columns,
        frameon=False,
        fontsize=LEGEND_FONT_SIZE,
        columnspacing=0.65,
        handlelength=1.0,
        handletextpad=0.3,
        labelspacing=0.1,
        borderaxespad=0.0,
    )


def add_top_figure_legend(
    figure, handles, labels, *, columns: int
) -> None:
    figure.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, TOP_LEGEND_Y),
        ncol=columns,
        frameon=False,
        fontsize=LEGEND_FONT_SIZE,
        columnspacing=0.65,
        handlelength=1.0,
        handletextpad=0.3,
        labelspacing=0.1,
        borderaxespad=0.0,
    )


def style_axis(axis) -> None:
    axis.grid(True, color="#D7D7D7", linewidth=0.65, alpha=0.8)
    axis.set_axisbelow(True)
    for spine in axis.spines.values():
        spine.set_color("#777777")


def plot_synthetic_linear_counting(axis, summary: pd.DataFrame) -> None:
    for bitmap_bits in sorted(summary.bitmap_bits.unique()):
        data = summary[summary.bitmap_bits == bitmap_bits]
        y = np.maximum(data.p95_absolute_relative_error_percent, 0.01)
        axis.plot(
            data.true_count,
            y,
            marker="o",
            markersize=2.8,
            linewidth=1.2,
            label=f"{bitmap_bits} bits",
        )
    axis.axvspan(16, 128, color="#BBBBBB", alpha=0.16, linewidth=0)
    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    axis.set_xlabel("Distinct flows in one epoch")
    axis.set_ylabel("p95 count error (%)")
    style_axis(axis)


def plot_synthetic_flow_encoding(axis, frame: pd.DataFrame) -> None:
    for bits in sorted(frame.bits.unique()):
        data = frame[frame.bits == bits]
        axis.plot(
            data.true_count,
            data.relative_error * 100,
            linewidth=1.35,
            label=f"{bits} bits",
        )
    axis.axvspan(16, 128, color="#BBBBBB", alpha=0.16, linewidth=0)
    axis.set_xscale("log", base=2)
    axis.set_xlabel("Exact flow count")
    axis.set_ylabel("Count overestimate (%)")
    style_axis(axis)


def plot_synthetic_utilization(axis, frame: pd.DataFrame) -> None:
    for bits in sorted(frame.bits.unique()):
        data = frame[frame.bits == bits]
        axis.plot(
            data.true_utilization,
            data.p95_absolute_relative_error * 100,
            linewidth=1.35,
            label=f"{bits} bits",
        )
    axis.set_xscale("log")
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    axis.xaxis.set_minor_locator(NullLocator())
    axis.set_xlabel("Exact utilization, U")
    axis.set_ylabel("p95 U error (%)")
    style_axis(axis)


def plot_representation_accuracy() -> None:
    linear = pd.read_csv(SYNTHETIC_ROOT / "linear_counting_samples.csv")
    flow_encoding = pd.read_csv(SYNTHETIC_ROOT / "flow_count_encoding.csv")
    utilization = pd.read_csv(SYNTHETIC_ROOT / "utilization_encoding.csv")
    linear_summary = (
        linear.groupby(["bitmap_bits", "true_count"], as_index=False)
        .agg(
            median_relative_error=("relative_error", "median"),
            p95_absolute_relative_error=(
                "absolute_relative_error",
                lambda values: values.quantile(0.95),
            ),
            saturation_probability=("saturated", "mean"),
            state_bytes_four_banks=("state_bytes_four_banks", "first"),
        )
    )
    linear_summary["p95_absolute_relative_error_percent"] = (
        linear_summary.p95_absolute_relative_error * 100
    )

    export_plot_dataframe(
        "figure1a_linear_counting_points.csv",
        linear_summary,
        base_dir=PLOT_DATA_ROOT,
        metadata={
            "independent_unit": "flow-ID pattern and hash seed",
            "bitmap_occupancy": "produced only by the real hash/mark algorithm",
        },
    )
    export_plot_dataframe(
        "figure1b_flow_count_encoding_points.csv",
        flow_encoding,
        base_dir=PLOT_DATA_ROOT,
        metadata={"mapping": "conservative N/S logarithmic encoding"},
    )
    export_plot_dataframe(
        "figure1c_utilization_encoding_points.csv",
        utilization,
        base_dir=PLOT_DATA_ROOT,
        metadata={"rounding": "1000 stochastic-rounding samples per point"},
    )

    plotting_functions = (
        (plot_synthetic_linear_counting, linear_summary, "figure1a_linear_counting.pdf"),
        (plot_synthetic_flow_encoding, flow_encoding, "figure1b_flow_count_encoding.pdf"),
        (plot_synthetic_utilization, utilization, "figure1c_utilization_encoding.pdf"),
    )
    for function, data, filename in plotting_functions:
        figure, axis = plt.subplots(figsize=PANEL_FIGSIZE)
        function(axis, data)
        _handles, labels = axis.get_legend_handles_labels()
        columns = 3 if len(labels) > 4 else len(labels)
        add_top_axis_legend(axis, columns=columns)
        save_figure(figure, filename)

    figure, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE)
    legends = []
    for axis, (function, data, _filename) in zip(
        axes, plotting_functions, strict=True
    ):
        function(axis, data)
        handles, labels = axis.get_legend_handles_labels()
        columns = 3 if len(labels) > 4 else len(labels)
        legends.append((axis, handles, labels, columns))
    figure.subplots_adjust(wspace=0.5)
    for axis, handles, labels, columns in legends:
        add_top_axis_legend(
            axis, handles, labels, columns=columns
        )
    save_figure(figure, "figure1_representation_accuracy.pdf")


def event_binned_values(
    times: np.ndarray,
    values: np.ndarray,
    trace: dict,
    metric: str,
    *,
    normalize_goodput: bool = False,
) -> pd.DataFrame:
    rows = []
    for state in trace["states"][1:]:
        reconnect = float(state["reconnect_time_s"])
        rtt_s = float(state["rtt_ms"]) / 1000
        end = reconnect + EVENT_WINDOW_RTTS * rtt_s
        mask = (times >= reconnect) & (times < end)
        if not np.any(mask):
            continue
        relative_rtts = (times[mask] - reconnect) / rtt_s
        selected_values = values[mask].astype(float)
        if normalize_goodput:
            selected_values = (
                selected_values / (float(state["bandwidth_mbps"]) * 1_000_000)
                * 100
            )
        bins = np.floor(relative_rtts / EVENT_BIN_RTTS).astype(int)
        for bin_index, value in zip(bins, selected_values):
            if 0 <= bin_index < EVENT_WINDOW_RTTS / EVENT_BIN_RTTS:
                rows.append(
                    {
                        "event": int(state["state_index"]),
                        "bin": int(bin_index),
                        "rtts_after_reconnect": (
                            int(bin_index) + 0.5
                        )
                        * EVENT_BIN_RTTS,
                        "metric": metric,
                        "value": float(value),
                    }
                )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"No event-aligned {metric} samples")
    event_means = (
        frame.groupby(
            ["event", "bin", "rtts_after_reconnect", "metric"],
            as_index=False,
        ).value.mean()
    )
    return (
        event_means.groupby(
            ["bin", "rtts_after_reconnect", "metric"], as_index=False
        ).value.mean()
    )


def collect_feedback_probability_series() -> pd.DataFrame:
    rows = []
    for case in feedback_analysis_cases():
        trace = load_trace(case.run)
        goodput = restore_remove_repeats(
            load_per_flow_metric(case, "goodput")
        )
        expected_flows = set(range(case.workload.persistent_flows))
        missing_flows = sorted(expected_flows - set(goodput.columns))
        if missing_flows:
            raise RuntimeError(
                f"Missing persistent-flow goodput vectors for "
                f"{case.config_name}: {missing_flows}"
            )

        aggregate_goodput = goodput.reindex(
            columns=sorted(expected_flows)
        ).sum(axis=1)
        frame = event_binned_values(
            aggregate_goodput.index.to_numpy(dtype=float),
            aggregate_goodput.to_numpy(dtype=float),
            trace,
            "normalized_goodput_percent",
            normalize_goodput=True,
        )
        frame["variant"] = case.variant.key
        frame["variant_label"] = case.variant.label
        frame["feedback_probability"] = case.variant.feedback_probability
        frame["run"] = case.run
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def remove_obsolete_figure2_outputs() -> None:
    old_figures = (
        "figure2a_total_flow_count.pdf",
        "figure2b_initial_flow_count.pdf",
        "figure2c_persistent_goodput.pdf",
        "figure2_flow_count_isolation.pdf",
    )
    old_data = (
        "figure2_flow_count_isolation_run_metrics.csv",
        "figure2_flow_count_isolation_points.csv",
    )
    for filename in old_figures:
        (PAPER_PLOT_ROOT / filename).unlink(missing_ok=True)
    for filename in old_data:
        path = PLOT_DATA_ROOT / filename
        path.unlink(missing_ok=True)
        path.with_suffix(path.suffix + ".metadata.json").unlink(
            missing_ok=True
        )


def plot_feedback_probability() -> None:
    remove_obsolete_figure2_outputs()
    run_series = collect_feedback_probability_series()
    run_metrics = (
        run_series.groupby(
            [
                "variant",
                "variant_label",
                "feedback_probability",
                "run",
            ],
            as_index=False,
        ).value.mean()
        .rename(columns={"value": "post_handover_goodput_percent"})
    )
    summary = summarize(
        run_metrics,
        ["variant", "variant_label", "feedback_probability"],
        "post_handover_goodput_percent",
    )

    export_plot_dataframe(
        "figure2_feedback_probability_run_series.csv",
        run_series,
        base_dir=PLOT_DATA_ROOT,
        metadata={
            "workload": "64 persistent flows",
            "feedback_probabilities": [
                variant.feedback_probability for variant in FEEDBACK_VARIANTS
            ],
            "event_window": "first 10 RTTs after path reconnection",
            "aggregation": (
                "normalized-time bins are averaged across handovers within "
                "each run; confidence intervals are calculated across ten "
                "matched runs"
            ),
        },
    )
    export_plot_dataframe(
        "figure2_feedback_probability_run_metrics.csv",
        run_metrics,
        base_dir=PLOT_DATA_ROOT,
    )
    export_plot_dataframe(
        "figure2_feedback_probability_points.csv",
        summary,
        base_dir=PLOT_DATA_ROOT,
    )

    ordered = summary.set_index("variant").loc[
        [variant.key for variant in FEEDBACK_VARIANTS]
    ].reset_index()
    x_values = np.arange(len(FEEDBACK_VARIANTS))
    figure, axis = plt.subplots(figsize=PANEL_FIGSIZE)
    color = PROTOCOL_COLORS["orbtcp_pint"]
    axis.errorbar(
        x_values,
        ordered["mean"],
        yerr=ordered.ci95,
        color=color,
        marker="o",
        linewidth=1.55,
        markersize=4.5,
        capsize=2.5,
    )
    axis.set_xticks(x_values)
    axis.set_xticklabels(
        [
            "1"
            if np.isclose(variant.feedback_probability, 1.0)
            else f"1/{round(1 / variant.feedback_probability)}"
            for variant in FEEDBACK_VARIANTS
        ]
    )
    axis.set_xlabel("Feedback probability, p")
    axis.set_ylabel("Post-handover goodput\n(% capacity)")
    upper_bound = float((ordered["mean"] + ordered.ci95).max())
    axis.set_ylim(0, max(105, math.ceil(upper_bound / 5) * 5))
    style_axis(axis)
    save_figure(figure, "figure2_feedback_probability.pdf")


def collect_handover_series() -> pd.DataFrame:
    rows = []
    for case in handover_cases():
        trace = load_trace(case.run)
        goodput = restore_remove_repeats(
            load_per_flow_metric(case, "goodput")
        ).sum(axis=1)
        queue_delay = load_queue_metric(case, "persistentQueueingDelay")
        utilization_error = load_utilization_error(case)
        frames = (
            event_binned_values(
                goodput.index.to_numpy(dtype=float),
                goodput.to_numpy(dtype=float),
                trace,
                "normalized_goodput_percent",
                normalize_goodput=True,
            ),
            event_binned_values(
                queue_delay.time.to_numpy(dtype=float),
                queue_delay.persistentQueueingDelay.to_numpy(dtype=float)
                * 1000,
                trace,
                "queue_delay_ms",
            ),
            event_binned_values(
                utilization_error.time.to_numpy(dtype=float),
                utilization_error.u_absolute_relative_error_percent.to_numpy(
                    dtype=float
                ),
                trace,
                "u_absolute_relative_error_percent",
            ),
        )
        for frame in frames:
            frame["variant"] = case.variant.key
            frame["variant_label"] = case.variant.label
            frame["run"] = case.run
            rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def plot_handover_panel(axis, summary, metric, ylabel) -> None:
    metric_data = summary[summary.metric == metric]
    for variant in HANDOVER_VARIANTS:
        data = metric_data[metric_data.variant == variant.key]
        color = VARIANT_COLORS[variant.key]
        axis.plot(
            data.rtts_after_reconnect,
            data["mean"],
            color=color,
            linewidth=1.55,
            label=variant.label,
        )
        axis.fill_between(
            data.rtts_after_reconnect,
            data["mean"] - data.ci95,
            data["mean"] + data.ci95,
            color=color,
            alpha=0.14,
            linewidth=0,
        )
    axis.set_xlabel("RTTs after reconnection")
    axis.set_ylabel(ylabel)
    axis.set_xlim(0, EVENT_WINDOW_RTTS)
    style_axis(axis)


def plot_handover_response() -> None:
    run_series = collect_handover_series()
    summary = summarize(
        run_series,
        [
            "variant",
            "variant_label",
            "metric",
            "bin",
            "rtts_after_reconnect",
        ],
        "value",
    )
    export_plot_dataframe(
        "figure3_handover_response_run_series.csv",
        run_series,
        base_dir=PLOT_DATA_ROOT,
        metadata={
            "aggregation": (
                "samples are averaged within each handover, handovers within "
                "each run, then confidence intervals are calculated across runs"
            ),
            "event_origin": "path reconnection, not disconnection",
        },
    )
    export_plot_dataframe(
        "figure3_handover_response_points.csv",
        summary,
        base_dir=PLOT_DATA_ROOT,
    )
    panel_specs = (
        (
            "normalized_goodput_percent",
            "Goodput (% capacity)",
            "figure3a_handover_goodput.pdf",
        ),
        ("queue_delay_ms", "Queue delay (ms)", "figure3b_handover_delay.pdf"),
        (
            "u_absolute_relative_error_percent",
            "Absolute U error (%)",
            "figure3c_handover_u_error.pdf",
        ),
    )
    handles = [
        Line2D([], [], color=VARIANT_COLORS[v.key], linewidth=1.8)
        for v in HANDOVER_VARIANTS
    ]
    labels = [COMPACT_VARIANT_LABELS[v.key] for v in HANDOVER_VARIANTS]
    for metric, ylabel, filename in panel_specs:
        figure, axis = plt.subplots(figsize=PANEL_FIGSIZE)
        plot_handover_panel(axis, summary, metric, ylabel)
        add_top_axis_legend(
            axis, handles, labels, columns=2
        )
        save_figure(figure, filename)

    figure, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE)
    for axis, (metric, ylabel, _filename) in zip(
        axes, panel_specs, strict=True
    ):
        plot_handover_panel(axis, summary, metric, ylabel)
    figure.subplots_adjust(wspace=0.5)
    add_top_figure_legend(
        figure, handles, labels, columns=len(handles)
    )
    save_figure(figure, "figure3_handover_response.pdf")


def stable_state_windows(trace: dict):
    states = trace["states"]
    for index, state in enumerate(states):
        start = float(state["reconnect_time_s"])
        stable_start = start + 5 * float(state["rtt_ms"]) / 1000
        end = (
            float(states[index + 1]["handover_time_s"])
            if index + 1 < len(states)
            else SIMULATION_TIME_S
        )
        if stable_start < end:
            yield state, stable_start, end


def jain_fairness(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    denominator = len(values) * float(np.sum(values**2))
    return float(np.sum(values) ** 2 / denominator) if denominator > 0 else 0.0


def collect_validation_metrics() -> pd.DataFrame:
    rows = []
    for case in validation_cases():
        trace = load_trace(case.run)
        goodput = restore_remove_repeats(
            load_per_flow_metric(case, "goodput")
        )
        try:
            retransmission = restore_remove_repeats(
                load_per_flow_metric(case, "retransmissionRate")
            )
        except (FileNotFoundError, RuntimeError):
            retransmission = None
        queue_delay = load_queue_metric(case, "persistentQueueingDelay")
        state_goodput = []
        state_fairness = []
        state_queue_p95 = []
        state_retransmission = []
        for state, start, end in stable_state_windows(trace):
            goodput_window = goodput[(goodput.index >= start) & (goodput.index < end)]
            retransmission_window = (
                retransmission[
                    (retransmission.index >= start)
                    & (retransmission.index < end)
                ]
                if retransmission is not None
                else pd.DataFrame()
            )
            queue_window = queue_delay[
                queue_delay.time.between(start, end, inclusive="left")
            ]
            if goodput_window.empty or queue_window.empty:
                continue
            per_flow_means = goodput_window.mean(axis=0).to_numpy(dtype=float)
            state_goodput.append(
                float(goodput_window.sum(axis=1).mean())
                / (float(state["bandwidth_mbps"]) * 1_000_000)
            )
            state_fairness.append(jain_fairness(per_flow_means))
            state_queue_p95.append(
                float(queue_window.persistentQueueingDelay.quantile(0.95)) * 1000
            )
            if not retransmission_window.empty:
                state_retransmission.append(
                    float(retransmission_window.sum(axis=1).mean()) / 1_000_000
                )
        if not state_goodput or not state_queue_p95:
            raise RuntimeError(
                f"Incomplete stable-state validation data for {case.config_name}"
            )
        rows.append(
            {
                "variant": case.variant.key,
                "variant_label": case.variant.label,
                "condition": case.condition.key,
                "condition_label": case.condition.label,
                "flow_count": case.workload.persistent_flows,
                "run": case.run,
                "normalized_goodput": float(np.mean(state_goodput)),
                "mean_epoch_p95_queue_delay_ms": float(
                    np.mean(state_queue_p95)
                ),
                "jain_fairness": float(np.mean(state_fairness)),
                "aggregate_retransmission_mbps": (
                    float(np.mean(state_retransmission))
                    if state_retransmission
                    else 0.0
                ),
            }
        )
    return pd.DataFrame(rows)


def validation_style(variant, condition_key: str) -> tuple[str, str, str]:
    color = VARIANT_COLORS[variant.key]
    linestyle = "-" if condition_key == DISTRIBUTED_NO_LOSS.key else "--"
    marker = VARIANT_MARKERS[variant.key]
    return color, linestyle, marker


def plot_validation_panel(axis, summary, metric, ylabel, scale=1.0) -> None:
    for condition_key in summary.condition.unique():
        for variant in VALIDATION_VARIANTS:
            data = summary[
                (summary.condition == condition_key)
                & (summary.variant == variant.key)
            ]
            color, linestyle, marker = validation_style(variant, condition_key)
            axis.errorbar(
                data.flow_count,
                data["mean"] * scale,
                yerr=data.ci95 * scale,
                color=color,
                linestyle=linestyle,
                marker=marker,
                linewidth=1.45,
                markersize=4.5,
                capsize=2.5,
            )
    axis.set_xlabel("Persistent flows")
    axis.set_ylabel(ylabel)
    axis.set_xticks((16, 64, 128))
    style_axis(axis)


def plot_final_validation() -> None:
    run_metrics = collect_validation_metrics()
    metrics = (
        "normalized_goodput",
        "mean_epoch_p95_queue_delay_ms",
        "jain_fairness",
        "aggregate_retransmission_mbps",
    )
    summaries = {
        metric: summarize(
            run_metrics,
            [
                "variant",
                "variant_label",
                "condition",
                "condition_label",
                "flow_count",
            ],
            metric,
        )
        for metric in metrics
    }
    export_plot_dataframe(
        "figure4_final_validation_run_metrics.csv",
        run_metrics,
        base_dir=PLOT_DATA_ROOT,
        metadata={
            "steady_window": (
                "from 5 current-path RTTs after reconnection until the next "
                "15-second handover"
            ),
            "queue_metric": "mean across epochs of each epoch's p95 delay",
            "conditions_are_not_averaged_together": True,
        },
    )
    point_frames = []
    for metric, summary in summaries.items():
        copy = summary.copy()
        copy["metric"] = metric
        point_frames.append(copy)
    export_plot_dataframe(
        "figure4_final_validation_points.csv",
        pd.concat(point_frames, ignore_index=True),
        base_dir=PLOT_DATA_ROOT,
    )

    panel_specs = (
        (
            "normalized_goodput",
            "Goodput (% capacity)",
            100.0,
            "figure4a_final_goodput.pdf",
        ),
        (
            "mean_epoch_p95_queue_delay_ms",
            "Epoch p95 delay (ms)",
            1.0,
            "figure4b_final_delay.pdf",
        ),
        (
            "jain_fairness",
            "Jain fairness",
            1.0,
            "figure4c_final_fairness.pdf",
        ),
    )
    handles = [
        Line2D(
            [],
            [],
            color=VARIANT_COLORS[variant.key],
            marker=VARIANT_MARKERS[variant.key],
            linestyle="-",
        )
        for variant in VALIDATION_VARIANTS
    ]
    labels = [
        COMPACT_VARIANT_LABELS[variant.key]
        for variant in VALIDATION_VARIANTS
    ]
    handles.extend(
        (
            Line2D([], [], color="#555555", linestyle="-"),
            Line2D([], [], color="#555555", linestyle="--"),
        )
    )
    labels.extend(("Distributed/no loss", "Bottleneck/loss"))

    for metric, ylabel, scale, filename in panel_specs:
        figure, axis = plt.subplots(figsize=PANEL_FIGSIZE)
        plot_validation_panel(axis, summaries[metric], metric, ylabel, scale)
        add_top_axis_legend(
            axis, handles, labels, columns=2
        )
        save_figure(figure, filename)

    figure, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE)
    for axis, (metric, ylabel, scale, _filename) in zip(
        axes, panel_specs, strict=True
    ):
        plot_validation_panel(axis, summaries[metric], metric, ylabel, scale)
    figure.subplots_adjust(wspace=0.5)
    add_top_figure_legend(
        figure, handles, labels, columns=len(handles)
    )
    save_figure(figure, "figure4_final_validation.pdf")


def write_manifest() -> None:
    manifest = {
        "experiment": EXPERIMENT,
        "figures": {
            "figure1": "representation accuracy: Linear Counting, N/S encoding, U encoding",
            "figure2": "post-handover goodput sensitivity to feedback probability",
            "figure3": "event-aligned handover decomposition",
            "figure4": "Exact PINT versus final OrbCC validation",
        },
        "independent_network_runs": len(RUNS),
        "matched_simulation_configs": sum(1 for _case in cases()),
        "plot_data_directory": str(PLOT_DATA_ROOT),
    }
    PAPER_PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    (PAPER_PLOT_ROOT / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    PAPER_PLOT_ROOT.mkdir(parents=True, exist_ok=True)
    plot_representation_accuracy()
    plot_feedback_probability()
    plot_handover_response()
    plot_final_validation()
    write_manifest()


if __name__ == "__main__":
    main()
