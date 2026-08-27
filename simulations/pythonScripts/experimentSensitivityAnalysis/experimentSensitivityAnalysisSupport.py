#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
import math


EXPERIMENT = "experimentSensitivityAnalysis"
INI_FILE = f"{EXPERIMENT}.ini"
RUNS = range(1, 11)

SIMULATION_TIME_S = 300
HANDOVER_INTERVAL_S = 15
MIN_HANDOVER_DOWNTIME_MS = 45
MAX_HANDOVER_DOWNTIME_MS = 120
MIN_BANDWIDTH_MBPS = 50
MAX_BANDWIDTH_MBPS = 100
MIN_RTT_MS = 20
MAX_RTT_MS = 100
MIN_LOSS_PER = 0.0
MAX_LOSS_PER = 0.01

ACCESS_RATE = "10Gbps"
MSS_BYTES = 1448
FLOW_START_WINDOW_S = 1.0
TRANSIENT_HANDOVER_TIME_S = 60
TRANSIENT_START_SPREAD_S = 0.01
PERSISTENT_SEND_BYTES = "2GB"
LARGE_NON_BOTTLENECK_QUEUE_PACKETS = 100_000

# These are the current candidate values. The synthetic calibration is designed
# to justify or replace them before the final network cases are rerun.
SELECTED_SKETCH_BITS = 4096
SELECTED_FLOW_COUNT_BITS = 8
SELECTED_UTILIZATION_BITS = 8
PINT_MAX_FLOW_COUNT = 65_535
PINT_MAX_CONCURRENT_FLOWS = 512
PINT_MAX_UTILIZATION = 4.0
PINT_FEEDBACK_PROBABILITY = 1.0

SYNTHETIC_BITMAP_BITS = (256, 512, 1024, 2048, 4096, 8192)
SYNTHETIC_ENCODING_BITS = (4, 6, 8, 10)
SYNTHETIC_MAX_FLOWS = 65_536
SYNTHETIC_HASH_SEEDS = 200
SYNTHETIC_ID_PATTERNS = ("sequential", "random64")


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    config_label: str
    flow_count_sketch: bool
    flow_count_bits: int
    utilization_bits: int


EXACT_PINT = Variant("exact", "Exact PINT", "Exact", False, 0, 0)
LC_ONLY = Variant("lc_only", "Linear Counting", "LcOnly", True, 0, 0)
FLOW_ENCODING_ONLY = Variant(
    "flow_encoding_only",
    "N/S encoding",
    "FlowEncodingOnly",
    False,
    SELECTED_FLOW_COUNT_BITS,
    0,
)
LC_FLOW_ENCODING = Variant(
    "lc_flow_encoding",
    "Linear Counting + N/S encoding",
    "LcFlowEncoding",
    True,
    SELECTED_FLOW_COUNT_BITS,
    0,
)
UTILIZATION_ENCODING_ONLY = Variant(
    "utilization_encoding_only",
    "U encoding",
    "UtilizationEncodingOnly",
    False,
    0,
    SELECTED_UTILIZATION_BITS,
)
FINAL_ORBCC = Variant(
    "orbcc",
    "OrbCC",
    "OrbCC",
    True,
    SELECTED_FLOW_COUNT_BITS,
    SELECTED_UTILIZATION_BITS,
)

FLOW_ISOLATION_VARIANTS = (
    EXACT_PINT,
    LC_ONLY,
    FLOW_ENCODING_ONLY,
    LC_FLOW_ENCODING,
)
HANDOVER_VARIANTS = (
    EXACT_PINT,
    UTILIZATION_ENCODING_ONLY,
    LC_FLOW_ENCODING,
    FINAL_ORBCC,
)
VALIDATION_VARIANTS = (EXACT_PINT, FINAL_ORBCC)
ALL_VARIANTS = (
    EXACT_PINT,
    LC_ONLY,
    FLOW_ENCODING_ONLY,
    UTILIZATION_ENCODING_ONLY,
    LC_FLOW_ENCODING,
    FINAL_ORBCC,
)


@dataclass(frozen=True)
class Condition:
    key: str
    label: str
    config_label: str
    delay_mode: str
    has_loss: bool


DISTRIBUTED_NO_LOSS = Condition(
    "distributed_no_loss",
    "Distributed RTT, no loss",
    "DistributedNoLoss",
    "distributed",
    False,
)
BOTTLENECK_LOSS = Condition(
    "bottleneck_loss",
    "Bottleneck RTT, 0-1% loss",
    "BottleneckLoss",
    "bottleneck",
    True,
)
VALIDATION_CONDITIONS = (DISTRIBUTED_NO_LOSS, BOTTLENECK_LOSS)


@dataclass(frozen=True)
class Workload:
    experiment_key: str
    key: str
    label: str
    config_label: str
    persistent_flows: int
    transient_flows: int = 0
    transient_packets: int = 0

    @property
    def total_flows(self) -> int:
        return self.persistent_flows + self.transient_flows


FLOW_ISOLATION_WORKLOADS = tuple(
    Workload(
        "flow_isolation",
        f"transient_{transient_flows}",
        f"{transient_flows} one-packet transient flows",
        f"Transient{transient_flows}",
        persistent_flows=32,
        transient_flows=transient_flows,
        transient_packets=1 if transient_flows else 0,
    )
    for transient_flows in (0, 32, 128)
)

HANDOVER_WORKLOAD = Workload(
    "handover",
    "64flows",
    "64 persistent flows",
    "64Flows",
    persistent_flows=64,
)

VALIDATION_WORKLOADS = tuple(
    Workload(
        "validation",
        f"{flow_count}flows",
        f"{flow_count} persistent flows",
        f"{flow_count}Flows",
        persistent_flows=flow_count,
    )
    for flow_count in (16, 64, 128)
)


@dataclass(frozen=True)
class SimulationCase:
    variant: Variant
    workload: Workload
    condition: Condition
    run: int

    @property
    def config_name(self) -> str:
        experiment_label = {
            "flow_isolation": "FlowIsolation",
            "handover": "Handover",
            "validation": "Validation",
        }[self.workload.experiment_key]
        return (
            f"Sensitivity{experiment_label}_{self.variant.config_label}_"
            f"{self.workload.config_label}_{self.condition.config_label}_"
            f"Run{self.run}"
        )

    @property
    def scenario_name(self) -> str:
        return (
            f"{self.workload.experiment_key}_{self.workload.key}_"
            f"{self.condition.key}_run{self.run}"
        )


def flow_isolation_cases():
    for variant in FLOW_ISOLATION_VARIANTS:
        for workload in FLOW_ISOLATION_WORKLOADS:
            for run in RUNS:
                yield SimulationCase(
                    variant, workload, DISTRIBUTED_NO_LOSS, run
                )


def handover_cases():
    for variant in HANDOVER_VARIANTS:
        for run in RUNS:
            yield SimulationCase(
                variant, HANDOVER_WORKLOAD, DISTRIBUTED_NO_LOSS, run
            )


def validation_cases():
    for variant in VALIDATION_VARIANTS:
        for workload in VALIDATION_WORKLOADS:
            for condition in VALIDATION_CONDITIONS:
                for run in RUNS:
                    yield SimulationCase(variant, workload, condition, run)


def cases():
    yield from flow_isolation_cases()
    yield from handover_cases()
    yield from validation_cases()


def expected_simulation_count() -> int:
    return sum(1 for _case in cases())


def queue_packets(bandwidth_mbps: float, rtt_ms: float) -> int:
    if bandwidth_mbps <= 0 or rtt_ms <= 0:
        raise ValueError("bandwidth and RTT must be positive")
    bdp_bits = bandwidth_mbps * 1_000_000 * rtt_ms / 1000
    return max(1, math.ceil(bdp_bits / (8 * MSS_BYTES)))


def trace_name(run: int) -> str:
    return f"trace_run{run}"


def variant_by_key(key: str) -> Variant:
    for variant in ALL_VARIANTS:
        if variant.key == key:
            return variant
    raise KeyError(key)


__all__ = (
    "ACCESS_RATE",
    "ALL_VARIANTS",
    "BOTTLENECK_LOSS",
    "Condition",
    "DISTRIBUTED_NO_LOSS",
    "EXACT_PINT",
    "EXPERIMENT",
    "FINAL_ORBCC",
    "FLOW_ENCODING_ONLY",
    "FLOW_ISOLATION_VARIANTS",
    "FLOW_ISOLATION_WORKLOADS",
    "FLOW_START_WINDOW_S",
    "HANDOVER_INTERVAL_S",
    "HANDOVER_VARIANTS",
    "HANDOVER_WORKLOAD",
    "INI_FILE",
    "LARGE_NON_BOTTLENECK_QUEUE_PACKETS",
    "LC_FLOW_ENCODING",
    "LC_ONLY",
    "MAX_BANDWIDTH_MBPS",
    "MAX_HANDOVER_DOWNTIME_MS",
    "MAX_LOSS_PER",
    "MAX_RTT_MS",
    "MIN_BANDWIDTH_MBPS",
    "MIN_HANDOVER_DOWNTIME_MS",
    "MIN_LOSS_PER",
    "MIN_RTT_MS",
    "MSS_BYTES",
    "PERSISTENT_SEND_BYTES",
    "PINT_FEEDBACK_PROBABILITY",
    "PINT_MAX_CONCURRENT_FLOWS",
    "PINT_MAX_FLOW_COUNT",
    "PINT_MAX_UTILIZATION",
    "RUNS",
    "SELECTED_FLOW_COUNT_BITS",
    "SELECTED_SKETCH_BITS",
    "SELECTED_UTILIZATION_BITS",
    "SIMULATION_TIME_S",
    "SYNTHETIC_BITMAP_BITS",
    "SYNTHETIC_ENCODING_BITS",
    "SYNTHETIC_HASH_SEEDS",
    "SYNTHETIC_ID_PATTERNS",
    "SYNTHETIC_MAX_FLOWS",
    "SimulationCase",
    "TRANSIENT_HANDOVER_TIME_S",
    "TRANSIENT_START_SPREAD_S",
    "UTILIZATION_ENCODING_ONLY",
    "VALIDATION_CONDITIONS",
    "VALIDATION_VARIANTS",
    "VALIDATION_WORKLOADS",
    "Variant",
    "Workload",
    "cases",
    "expected_simulation_count",
    "flow_isolation_cases",
    "handover_cases",
    "queue_packets",
    "trace_name",
    "validation_cases",
    "variant_by_key",
)
