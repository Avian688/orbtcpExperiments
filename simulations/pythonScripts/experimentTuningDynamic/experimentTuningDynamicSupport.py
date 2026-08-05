#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "experimentTuning"))

from experimentTuningSupport import (  # noqa: E402
    EXACT_PINT,
    FLOW_COUNT_EXACT_VARIANTS,
    FLOW_COUNT_SKETCH_VARIANTS,
    FLOW_COUNT_VARIANTS,
    FULL_ORBCC,
    MSS_BYTES,
    PINT_VARIANTS,
    SAMPLING_VARIANTS,
    UTILIZATION_VARIANTS,
    VARIANTS,
    Variant,
    family_label,
    family_tick_labels,
    family_variant_series,
    family_x_label,
)


EXPERIMENT = "experimentTuningDynamic"
RUNS = range(1, 11)
FLOW_COUNTS = (5, 20, 100)
SIMULATION_TIME_S = 300
HANDOVER_INTERVAL_S = 15
MIN_HANDOVER_DOWNTIME_MS = 45
MAX_HANDOVER_DOWNTIME_MS = 120
MIN_BANDWIDTH_MBPS = 50
MAX_BANDWIDTH_MBPS = 100
MIN_RTT_MS = 1
MAX_RTT_MS = 100
MIN_LOSS_PER = 0.0
MAX_LOSS_PER = 0.01
FLOW_START_WINDOW_S = 1.0
QUEUE_BDP_MULTIPLIER = 2
REFERENCE_BANDWIDTH_MBPS = (MIN_BANDWIDTH_MBPS + MAX_BANDWIDTH_MBPS) / 2
REFERENCE_RTT_MS = (MIN_RTT_MS + MAX_RTT_MS) / 2
QUEUE_PACKETS = round(
    (
        REFERENCE_BANDWIDTH_MBPS
        * 125_000
        * (REFERENCE_RTT_MS / 1000)
        * QUEUE_BDP_MULTIPLIER
    )
    / MSS_BYTES
)
FAMILIES = ("flow_count", "utilization", "sampling")


@dataclass(frozen=True)
class Condition:
    key: str
    label: str
    config_label: str
    has_loss: bool


NO_LOSS = Condition("no_loss", "No loss", "NoLoss", False)
LOSS = Condition("loss", "Loss", "Loss", True)
CONDITIONS = (NO_LOSS, LOSS)


def ini_name(pint: bool) -> str:
    suffix = "orbtcp_pint" if pint else "orbtcp"
    return f"{EXPERIMENT}_{suffix}.ini"


def config_name(
    variant: Variant,
    flow_count: int,
    condition: Condition,
    run: int,
) -> str:
    return (
        f"{variant.config_prefix}_{flow_count}flows_"
        f"{condition.config_label}_Run{run}"
    )


def scenario_name(flow_count: int, condition: Condition, run: int) -> str:
    return f"{flow_count}flows_{condition.key}_run{run}"


def trace_name(run: int) -> str:
    return f"trace_run{run}"


def family_plot_variants(family: str) -> tuple[Variant, ...]:
    if family == "flow_count":
        return (
            FULL_ORBCC,
            *FLOW_COUNT_SKETCH_VARIANTS,
            *FLOW_COUNT_EXACT_VARIANTS,
            EXACT_PINT,
        )
    if family == "utilization":
        return (FULL_ORBCC, *UTILIZATION_VARIANTS, EXACT_PINT)
    if family == "sampling":
        return (FULL_ORBCC, *SAMPLING_VARIANTS, EXACT_PINT)
    raise ValueError(f"Unknown tuning family: {family}")


def cases():
    for variant in VARIANTS:
        for flow_count in FLOW_COUNTS:
            for condition in CONDITIONS:
                for run in RUNS:
                    yield variant, flow_count, condition, run


def expected_simulation_count() -> int:
    return len(VARIANTS) * len(FLOW_COUNTS) * len(CONDITIONS) * len(RUNS)


__all__ = (
    "CONDITIONS",
    "EXACT_PINT",
    "EXPERIMENT",
    "FAMILIES",
    "FLOW_COUNT_EXACT_VARIANTS",
    "FLOW_COUNT_SKETCH_VARIANTS",
    "FLOW_COUNT_VARIANTS",
    "FLOW_COUNTS",
    "FLOW_START_WINDOW_S",
    "FULL_ORBCC",
    "HANDOVER_INTERVAL_S",
    "LOSS",
    "MAX_BANDWIDTH_MBPS",
    "MAX_HANDOVER_DOWNTIME_MS",
    "MAX_LOSS_PER",
    "MAX_RTT_MS",
    "MIN_BANDWIDTH_MBPS",
    "MIN_HANDOVER_DOWNTIME_MS",
    "MIN_LOSS_PER",
    "MIN_RTT_MS",
    "MSS_BYTES",
    "NO_LOSS",
    "PINT_VARIANTS",
    "QUEUE_PACKETS",
    "RUNS",
    "SAMPLING_VARIANTS",
    "SIMULATION_TIME_S",
    "VARIANTS",
    "Variant",
    "UTILIZATION_VARIANTS",
    "cases",
    "config_name",
    "expected_simulation_count",
    "family_label",
    "family_plot_variants",
    "family_tick_labels",
    "family_variant_series",
    "family_x_label",
    "ini_name",
    "scenario_name",
    "trace_name",
)
