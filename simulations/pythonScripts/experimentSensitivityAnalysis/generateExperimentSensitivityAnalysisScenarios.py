#!/usr/bin/env python3

from __future__ import annotations

import json
import random
from pathlib import Path

from experimentSensitivityAnalysisSupport import (
    ACCESS_RATE,
    EXPERIMENT,
    HANDOVER_INTERVAL_S,
    MAX_BANDWIDTH_MBPS,
    MAX_HANDOVER_DOWNTIME_MS,
    MAX_LOSS_PER,
    MAX_RTT_MS,
    MIN_BANDWIDTH_MBPS,
    MIN_HANDOVER_DOWNTIME_MS,
    MIN_LOSS_PER,
    MIN_RTT_MS,
    RUNS,
    SIMULATION_TIME_S,
    Condition,
    SimulationCase,
    Workload,
    cases,
    queue_packets,
    trace_name,
)


SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = (
    SCRIPT_DIR / "../../paperExperiments/scenarios" / EXPERIMENT
).resolve()
TRACE_SEED = 84_113
STATE_COUNT = SIMULATION_TIME_S // HANDOVER_INTERVAL_S


def stratified_values(
    low: float,
    high: float,
    state_index: int,
    salt: int,
    *,
    integer: bool = False,
    decimals: int | None = None,
) -> list[float | int]:
    rng = random.Random(TRACE_SEED + salt * 10_000 + state_index)
    strata = list(range(len(RUNS)))
    rng.shuffle(strata)
    values = []
    for stratum in strata:
        fraction = (stratum + rng.random()) / len(strata)
        value = low + fraction * (high - low)
        if integer:
            value = int(round(value))
        elif decimals is not None:
            value = round(value, decimals)
        values.append(value)
    return values


def avoid_repeat(value, previous, low, high, step):
    if previous is None or value != previous:
        return value
    adjusted = value + step if value + step <= high else value - step
    return max(low, min(high, adjusted))


def build_traces() -> dict[int, list[dict[str, float | int | str | None]]]:
    traces = {run: [] for run in RUNS}
    for state_index in range(STATE_COUNT):
        bandwidths = stratified_values(
            MIN_BANDWIDTH_MBPS,
            MAX_BANDWIDTH_MBPS,
            state_index,
            1,
            decimals=2,
        )
        rtts = stratified_values(
            MIN_RTT_MS,
            MAX_RTT_MS,
            state_index,
            2,
            integer=True,
        )
        losses = stratified_values(
            MIN_LOSS_PER,
            MAX_LOSS_PER,
            state_index,
            3,
            decimals=4,
        )
        downtimes = stratified_values(
            MIN_HANDOVER_DOWNTIME_MS,
            MAX_HANDOVER_DOWNTIME_MS,
            state_index,
            4,
            integer=True,
        )

        for offset, run in enumerate(RUNS):
            previous = traces[run][-1] if traces[run] else None
            bandwidth = float(
                avoid_repeat(
                    float(bandwidths[offset]),
                    float(previous["bandwidth_mbps"]) if previous else None,
                    MIN_BANDWIDTH_MBPS,
                    MAX_BANDWIDTH_MBPS,
                    0.01,
                )
            )
            rtt = int(
                avoid_repeat(
                    int(rtts[offset]),
                    int(previous["rtt_ms"]) if previous else None,
                    MIN_RTT_MS,
                    MAX_RTT_MS,
                    1,
                )
            )
            handover_time = (
                state_index * HANDOVER_INTERVAL_S if state_index else None
            )
            downtime_ms = int(downtimes[offset]) if state_index else 0
            reconnect_time = (
                handover_time + downtime_ms / 1000
                if handover_time is not None
                else 0.0
            )
            traces[run].append(
                {
                    "state_index": state_index,
                    "active_path": "A" if state_index % 2 == 0 else "B",
                    "handover_time_s": handover_time,
                    "reconnect_time_s": reconnect_time,
                    "downtime_ms": downtime_ms,
                    "bandwidth_mbps": bandwidth,
                    "rtt_ms": rtt,
                    "loss_per": float(losses[offset]),
                    "queue_packets": queue_packets(bandwidth, rtt),
                }
            )
    return traces


def append_set_channel_parameter(
    lines: list[str], module: str, gate: int, parameter: str, value: str
) -> None:
    lines.append(
        f'        <set-channel-param src-module="{module}" '
        f'src-gate="pppg$o[{gate}]" par="{parameter}" value="{value}"/>'
    )


def path_gate(flow_count: int, path: str) -> int:
    return flow_count + (0 if path == "A" else 1)


def transit_module(path: str) -> str:
    return f"transit{path}"


def delays(condition: Condition, rtt_ms: float) -> tuple[float, float, float]:
    if condition.delay_mode == "distributed":
        per_link = rtt_ms / 8
        return per_link, per_link, per_link
    if condition.delay_mode == "bottleneck":
        return 0.0, 0.0, rtt_ms / 2
    raise ValueError(f"Unknown delay mode: {condition.delay_mode}")


def append_access_parameters(
    lines: list[str], workload: Workload, condition: Condition, state: dict,
    *, set_rate: bool,
) -> None:
    access_delay, _transit_delay, _bottleneck_delay = delays(
        condition, float(state["rtt_ms"])
    )
    for flow_index in range(workload.total_flows):
        for module, gate in (
            (f"client[{flow_index}]", 0),
            ("ingress", flow_index),
            (f"server[{flow_index}]", 0),
            ("egress", flow_index),
        ):
            append_set_channel_parameter(
                lines, module, gate, "delay", f"{access_delay:.12g}ms"
            )
            if set_rate:
                append_set_channel_parameter(
                    lines, module, gate, "datarate", ACCESS_RATE
                )


def append_existing_path_parameters(
    lines: list[str], workload: Workload, condition: Condition, state: dict,
    path: str,
) -> None:
    _access_delay, transit_delay, bottleneck_delay = delays(
        condition, float(state["rtt_ms"])
    )
    gate = path_gate(workload.total_flows, path)
    transit = transit_module(path)
    bandwidth = float(state["bandwidth_mbps"])
    forward_loss = float(state["loss_per"]) if condition.has_loss else 0.0

    for module, module_gate in (("ingress", gate), (transit, 0)):
        append_set_channel_parameter(
            lines, module, module_gate, "delay", f"{transit_delay:.12g}ms"
        )
        append_set_channel_parameter(
            lines, module, module_gate, "datarate", ACCESS_RATE
        )
        append_set_channel_parameter(lines, module, module_gate, "per", "0")

    for module, module_gate in ((transit, 1), ("egress", gate)):
        append_set_channel_parameter(
            lines,
            module,
            module_gate,
            "delay",
            f"{bottleneck_delay:.12g}ms",
        )
        append_set_channel_parameter(
            lines,
            module,
            module_gate,
            "datarate",
            f"{bandwidth:.12g}Mbps",
        )
    append_set_channel_parameter(lines, transit, 1, "per", f"{forward_loss:.12g}")
    append_set_channel_parameter(lines, "egress", gate, "per", "0")


def path_endpoints(workload: Workload, path: str):
    gate = path_gate(workload.total_flows, path)
    transit = transit_module(path)
    return (
        ("ingress", gate),
        (transit, 0),
        (transit, 1),
        ("egress", gate),
    )


def append_disconnect_path(lines: list[str], workload: Workload, path: str) -> None:
    for module, gate in path_endpoints(workload, path):
        lines.append(
            f'        <disconnect src-module="{module}" '
            f'src-gate="pppg$o[{gate}]"/>'
        )


def append_crash_path(lines: list[str], workload: Workload, path: str) -> None:
    for module, gate in path_endpoints(workload, path):
        lines.append(f'        <crash module="{module}.ppp[{gate}]"/>')


def append_start_path(lines: list[str], workload: Workload, path: str) -> None:
    for module, gate in path_endpoints(workload, path):
        lines.append(f'        <start module="{module}.ppp[{gate}]"/>')


def append_connect(
    lines: list[str], source: str, source_gate: int, destination: str,
    destination_gate: int, datarate: str, delay_ms: float, per: float = 0,
) -> None:
    lines.append(
        f'        <connect src-module="{source}" src-gate="pppg$o[{source_gate}]"'
    )
    lines.append(
        f'                 dest-module="{destination}" '
        f'dest-gate="pppg$i[{destination_gate}]"'
    )
    lines.append('                 channel-type="ned.DatarateChannel">')
    lines.append(f'                 <param name="datarate" value="{datarate}" />')
    lines.append(f'                 <param name="delay" value="{delay_ms:.12g}ms" />')
    lines.append(f'                 <param name="per" value="{per:.12g}" />')
    lines.append("        </connect>")


def append_connect_path(
    lines: list[str], workload: Workload, condition: Condition, state: dict,
    path: str,
) -> None:
    _access_delay, transit_delay, bottleneck_delay = delays(
        condition, float(state["rtt_ms"])
    )
    gate = path_gate(workload.total_flows, path)
    transit = transit_module(path)
    bandwidth = f'{float(state["bandwidth_mbps"]):.12g}Mbps'
    forward_loss = float(state["loss_per"]) if condition.has_loss else 0.0

    append_connect(lines, "ingress", gate, transit, 0, ACCESS_RATE, transit_delay)
    append_connect(lines, transit, 0, "ingress", gate, ACCESS_RATE, transit_delay)
    append_connect(
        lines, transit, 1, "egress", gate, bandwidth, bottleneck_delay,
        forward_loss,
    )
    append_connect(lines, "egress", gate, transit, 1, bandwidth, bottleneck_delay)


def append_queue_capacity(lines: list[str], state: dict, path: str) -> None:
    lines.append(
        f'        <set-param module="{transit_module(path)}.ppp[1].queue" '
        f'par="packetCapacity" value="{int(state["queue_packets"])}"/>'
    )


def append_initial_state(
    lines: list[str], workload: Workload, condition: Condition, state: dict
) -> None:
    lines.append('    <at t="0">')
    append_access_parameters(lines, workload, condition, state, set_rate=True)
    append_existing_path_parameters(lines, workload, condition, state, "A")
    append_existing_path_parameters(lines, workload, condition, state, "B")
    append_queue_capacity(lines, state, "A")
    append_queue_capacity(lines, state, "B")
    append_disconnect_path(lines, workload, "B")
    append_crash_path(lines, workload, "B")
    lines.append('        <update module="configurator"/>')
    lines.append("    </at>")


def append_handover_start(
    lines: list[str], workload: Workload, previous_state: dict, state: dict
) -> None:
    lines.append(f'    <at t="{int(state["handover_time_s"])}">')
    append_disconnect_path(lines, workload, str(previous_state["active_path"]))
    append_crash_path(lines, workload, str(previous_state["active_path"]))
    lines.append("    </at>")


def append_handover_end(
    lines: list[str], workload: Workload, condition: Condition, state: dict
) -> None:
    reconnect_time = float(state["reconnect_time_s"])
    active_path = str(state["active_path"])
    lines.append(f'    <at t="{reconnect_time:.6f}">')
    append_connect_path(lines, workload, condition, state, active_path)
    append_start_path(lines, workload, active_path)
    append_queue_capacity(lines, state, active_path)
    append_access_parameters(lines, workload, condition, state, set_rate=False)
    lines.append('        <update module="configurator"/>')
    lines.append("    </at>")


def write_scenario(
    path: Path, workload: Workload, condition: Condition, states: list[dict]
) -> None:
    lines = ["<scenario>"]
    append_initial_state(lines, workload, condition, states[0])
    for previous_state, state in zip(states, states[1:]):
        append_handover_start(lines, workload, previous_state, state)
        append_handover_end(lines, workload, condition, state)
    lines.append("</scenario>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def unique_scenarios() -> dict[str, SimulationCase]:
    scenarios = {}
    for case in cases():
        scenarios.setdefault(case.scenario_name, case)
    return scenarios


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    traces = build_traces()
    for run, states in traces.items():
        (OUT_DIR / f"{trace_name(run)}.json").write_text(
            json.dumps(
                {
                    "run": run,
                    "simulation_time_s": SIMULATION_TIME_S,
                    "handover_interval_s": HANDOVER_INTERVAL_S,
                    "bandwidth_range_mbps": [
                        MIN_BANDWIDTH_MBPS,
                        MAX_BANDWIDTH_MBPS,
                    ],
                    "rtt_range_ms": [MIN_RTT_MS, MAX_RTT_MS],
                    "queue_policy": "one current-path BDP in 1448-byte packets",
                    "path_policy": "alternate distinct transit routers A and B",
                    "states": states,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    scenarios = unique_scenarios()
    for scenario, case in scenarios.items():
        write_scenario(
            OUT_DIR / f"{scenario}.xml",
            case.workload,
            case.condition,
            traces[case.run],
        )
    print(
        f"Generated {len(scenarios)} matched dual-path scenarios and "
        f"{len(RUNS)} traces for {EXPERIMENT}."
    )


if __name__ == "__main__":
    main()
