#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass


EXPERIMENT = "experimentTuning"
RUNS = range(1, 6)
FLOW_COUNTS = (5, 20, 100)
RTT_MS = 50
# Keep the fair-share operating point comparable while varying flow count.
BANDWIDTH_PER_FLOW_MBPS = 6
HANDOVER_INTERVAL_S = 15
MIN_HANDOVER_DOWNTIME_MS = 45
MAX_HANDOVER_DOWNTIME_MS = 120
SIMULATION_TIME_S = 250
EVALUATION_START_S = 110
EVALUATION_END_S = 240
FLOW_JOIN_WINDOW_S = 100
MSS_BYTES = 1448
QUEUE_BDP_MULTIPLIER = 1


def bottleneck_bandwidth_mbps(flow_count: int) -> int:
    if flow_count <= 0:
        raise ValueError("flow_count must be positive")
    return flow_count * BANDWIDTH_PER_FLOW_MBPS


def fair_share_bdp_packets(
    bandwidth_per_flow_mbps: float = BANDWIDTH_PER_FLOW_MBPS,
    rtt_ms: float = RTT_MS,
) -> float:
    return bandwidth_per_flow_mbps * 125_000 * (rtt_ms / 1000) / MSS_BYTES


def queue_packets(flow_count: int) -> int:
    return round(
        fair_share_bdp_packets()
        * flow_count
        * QUEUE_BDP_MULTIPLIER
    )


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    config_prefix: str
    family: str
    flow_count_bits: int | None = None
    flow_count_sketch: bool | None = None
    utilization_bits: int | None = None
    feedback_probability: float | None = None

    @property
    def is_pint(self) -> bool:
        return self.flow_count_bits is not None


FULL_ORBCC = Variant(
    key="orbtcp",
    label="Full INT reference",
    config_prefix="Orbtcp",
    family="reference",
)

EXACT_PINT = Variant(
    key="pint_exact",
    label="Exact PINT control",
    config_prefix="OrbtcpPintExact",
    family="exact",
    flow_count_bits=0,
    flow_count_sketch=False,
    utilization_bits=0,
    feedback_probability=1.0,
)

FLOW_COUNT_SKETCH_VARIANTS = (
    Variant("pint_flow_4", "4 bits", "OrbtcpPintFlow4", "flow_count", 4, True, 0, 1.0),
    Variant("pint_flow_6", "6 bits", "OrbtcpPintFlow6", "flow_count", 6, True, 0, 1.0),
    Variant("pint_flow_8", "8 bits", "OrbtcpPintFlow8", "flow_count", 8, True, 0, 1.0),
    Variant("pint_flow_10", "10 bits", "OrbtcpPintFlow10", "flow_count", 10, True, 0, 1.0),
)

FLOW_COUNT_EXACT_VARIANTS = (
    Variant("pint_flow_exact_4", "4 bits, exact count", "OrbtcpPintFlowExact4", "flow_count", 4, False, 0, 1.0),
    Variant("pint_flow_exact_6", "6 bits, exact count", "OrbtcpPintFlowExact6", "flow_count", 6, False, 0, 1.0),
    Variant("pint_flow_exact_8", "8 bits, exact count", "OrbtcpPintFlowExact8", "flow_count", 8, False, 0, 1.0),
    Variant("pint_flow_exact_10", "10 bits, exact count", "OrbtcpPintFlowExact10", "flow_count", 10, False, 0, 1.0),
)

FLOW_COUNT_VARIANTS = (
    *FLOW_COUNT_SKETCH_VARIANTS,
    *FLOW_COUNT_EXACT_VARIANTS,
)

UTILIZATION_VARIANTS = (
    Variant("pint_u_4", "4 bits", "OrbtcpPintU4", "utilization", 0, False, 4, 1.0),
    Variant("pint_u_6", "6 bits", "OrbtcpPintU6", "utilization", 0, False, 6, 1.0),
    Variant("pint_u_8", "8 bits", "OrbtcpPintU8", "utilization", 0, False, 8, 1.0),
    Variant("pint_u_10", "10 bits", "OrbtcpPintU10", "utilization", 0, False, 10, 1.0),
)

SAMPLING_VARIANTS = (
    Variant("pint_p_1_256", "p=1/256", "OrbtcpPintP1_256", "sampling", 0, False, 0, 1 / 256),
    Variant("pint_p_1_64", "p=1/64", "OrbtcpPintP1_64", "sampling", 0, False, 0, 1 / 64),
    Variant("pint_p_1_16", "p=1/16", "OrbtcpPintP1_16", "sampling", 0, False, 0, 1 / 16),
    Variant("pint_p_1_4", "p=1/4", "OrbtcpPintP1_4", "sampling", 0, False, 0, 1 / 4),
)

PINT_VARIANTS = (
    EXACT_PINT,
    *FLOW_COUNT_VARIANTS,
    *UTILIZATION_VARIANTS,
    *SAMPLING_VARIANTS,
)
VARIANTS = (FULL_ORBCC, *PINT_VARIANTS)
FAMILIES = ("flow_count", "utilization", "sampling")


def family_variants(family: str) -> tuple[Variant, ...]:
    if family == "flow_count":
        return (*FLOW_COUNT_VARIANTS, EXACT_PINT)
    if family == "utilization":
        return (*UTILIZATION_VARIANTS, EXACT_PINT)
    if family == "sampling":
        return (*SAMPLING_VARIANTS, EXACT_PINT)
    raise ValueError(f"Unknown tuning family: {family}")


def family_variant_series(
    family: str,
) -> tuple[tuple[str, tuple[Variant, ...]], ...]:
    if family == "flow_count":
        return (
            ("Sketch-derived count", (*FLOW_COUNT_SKETCH_VARIANTS, EXACT_PINT)),
            ("Exact count", (*FLOW_COUNT_EXACT_VARIANTS, EXACT_PINT)),
        )
    return (("OrbCC", family_variants(family)),)


def family_label(family: str) -> str:
    return {
        "flow_count": "Flow-count encoding",
        "utilization": "Utilization encoding",
        "sampling": "Feedback sampling",
    }[family]


def family_x_label(family: str) -> str:
    return {
        "flow_count": "Flow-count field budget",
        "utilization": "Utilization field budget",
        "sampling": "Feedback probability",
    }[family]


def family_tick_labels(family: str) -> tuple[str, ...]:
    if family == "flow_count":
        return ("4", "6", "8", "10", "Exact\n(16-bit)")
    if family == "utilization":
        return ("4", "6", "8", "10", "Exact")
    if family == "sampling":
        return ("1/256", "1/64", "1/16", "1/4", "1")
    raise ValueError(f"Unknown tuning family: {family}")


def ini_name(pint: bool) -> str:
    suffix = "orbtcp_pint" if pint else "orbtcp"
    return f"{EXPERIMENT}_{suffix}.ini"


def config_name(variant: Variant, flow_count: int, run: int) -> str:
    return f"{variant.config_prefix}_{flow_count}flows_{RTT_MS}ms_Run{run}"


def scenario_name(flow_count: int, run: int) -> str:
    return f"{flow_count}flows_{RTT_MS}ms_run{run}"
