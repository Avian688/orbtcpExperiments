#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass


EXPERIMENT = "experiment13"
RUNS = range(1, 6)
WORKLOADS = ("pathchange",)
SIMULATION_TIME_S = 300
HANDOVER_INTERVAL_S = 15
MSS_BYTES = 1448
QUEUE_PACKETS = 340


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    config_prefix: str
    protocol: str
    probability: float | None

    @property
    def is_pint(self) -> bool:
        return self.probability is not None


FULL_ORBCC = Variant(
    key="orbtcp",
    label="Full INT reference",
    config_prefix="Orbtcp",
    protocol="orbtcp",
    probability=None,
)

PINT_VARIANTS = (
    Variant("orbtcp_pint_p100", "p=100%", "OrbtcpPintP100", "orbtcp_pint", 1.0),
    Variant("orbtcp_pint_p50", "p=50%", "OrbtcpPintP50", "orbtcp_pint", 0.5),
    Variant("orbtcp_pint_p25", "p=25%", "OrbtcpPintP25", "orbtcp_pint", 0.25),
    Variant("orbtcp_pint_p12_5", "p=12.5%", "OrbtcpPintP12_5", "orbtcp_pint", 0.125),
    Variant("orbtcp_pint_p6_25", "p=6.25%", "OrbtcpPintP6_25", "orbtcp_pint", 0.0625),
    Variant("orbtcp_pint_p3_125", "p=3.125%", "OrbtcpPintP3_125", "orbtcp_pint", 0.03125),
    Variant("orbtcp_pint_p1_5625", "p=1.5625%", "OrbtcpPintP1_5625", "orbtcp_pint", 0.015625),
    Variant("orbtcp_pint_p0_78125", "p=0.78125%", "OrbtcpPintP0_78125", "orbtcp_pint", 0.0078125),
)
VARIANTS = (FULL_ORBCC, *PINT_VARIANTS)


def workload_label(workload: str) -> str:
    if workload == "pathchange":
        return "Path changes"
    raise ValueError(f"Unknown Experiment 13 workload: {workload}")


def workload_config_name(workload: str) -> str:
    if workload == "pathchange":
        return "PathChange"
    raise ValueError(f"Unknown Experiment 13 workload: {workload}")


def ini_name(variant: Variant) -> str:
    return f"{EXPERIMENT}_{'orbtcp_pint' if variant.is_pint else 'orbtcp'}.ini"


def config_name(variant: Variant, workload: str, run: int) -> str:
    return f"{variant.config_prefix}_{workload_config_name(workload)}_Run{run}"


def scenario_name(workload: str, run: int) -> str:
    return f"{workload}_run{run}"
