#!/usr/bin/env python3

from __future__ import annotations

import json
import random
from pathlib import Path

from experimentTuningDynamicSupport import (
    CONDITIONS,
    EXPERIMENT,
    FLOW_COUNTS,
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
    scenario_name,
    trace_name,
)


ACCESS_RATE = "10Gbps"
TRACE_SEED = 47_211
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


def avoid_integer_repeat(value: int, previous: int | None, low: int, high: int) -> int:
    if previous is None or value != previous:
        return value
    return value + 1 if value < high else value - 1


def build_traces() -> dict[int, list[dict[str, float | int | None]]]:
    traces = {run: [] for run in RUNS}
    for state_index in range(STATE_COUNT):
        bandwidths = stratified_values(
            MIN_BANDWIDTH_MBPS,
            MAX_BANDWIDTH_MBPS,
            state_index,
            1,
            integer=True,
        )
        rtts = stratified_values(
            MIN_RTT_MS,
            MAX_RTT_MS,
            state_index,
            2,
            integer=True,
        )
        loss_rates = stratified_values(
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

        for run_offset, run in enumerate(RUNS):
            previous = traces[run][-1] if traces[run] else None
            bandwidth = avoid_integer_repeat(
                int(bandwidths[run_offset]),
                int(previous["bandwidth_mbps"]) if previous else None,
                MIN_BANDWIDTH_MBPS,
                MAX_BANDWIDTH_MBPS,
            )
            rtt = avoid_integer_repeat(
                int(rtts[run_offset]),
                int(previous["rtt_ms"]) if previous else None,
                MIN_RTT_MS,
                MAX_RTT_MS,
            )
            handover_time_s = (
                state_index * HANDOVER_INTERVAL_S if state_index else None
            )
            downtime_ms = int(downtimes[run_offset]) if state_index else 0
            reconnect_time_s = (
                handover_time_s + downtime_ms / 1000
                if handover_time_s is not None
                else 0.0
            )
            traces[run].append(
                {
                    "state_index": state_index,
                    "handover_time_s": handover_time_s,
                    "reconnect_time_s": reconnect_time_s,
                    "downtime_ms": downtime_ms,
                    "bandwidth_mbps": bandwidth,
                    "rtt_ms": rtt,
                    "loss_per": float(loss_rates[run_offset]),
                }
            )
    return traces


def append_channel_parameter(
    lines: list[str], module: str, gate: int, parameter: str, value: str
) -> None:
    lines.append(
        f'        <set-channel-param src-module="{module}" '
        f'src-gate="pppg$o[{gate}]" par="{parameter}" value="{value}"/>'
    )


def append_access_path(
    lines: list[str], flow_count: int, one_way_link_delay_ms: float, set_rate: bool
) -> None:
    for index in range(flow_count):
        for module, gate in (
            (f"client[{index}]", 0),
            ("router1", index),
            (f"server[{index}]", 0),
            ("router2", index),
        ):
            append_channel_parameter(
                lines, module, gate, "delay", f"{one_way_link_delay_ms:.12g}ms"
            )
            if set_rate:
                append_channel_parameter(
                    lines, module, gate, "datarate", ACCESS_RATE
                )


def append_initial_state(
    lines: list[str], flow_count: int, state: dict, has_loss: bool
) -> None:
    one_way_link_delay_ms = float(state["rtt_ms"]) / 6
    forward_per = float(state["loss_per"]) if has_loss else 0.0
    lines.append('    <at t="0">')
    append_access_path(lines, flow_count, one_way_link_delay_ms, set_rate=True)
    for module in ("router1", "router2"):
        append_channel_parameter(
            lines,
            module,
            flow_count,
            "delay",
            f"{one_way_link_delay_ms:.12g}ms",
        )
        append_channel_parameter(
            lines,
            module,
            flow_count,
            "datarate",
            f'{int(state["bandwidth_mbps"])}Mbps',
        )
    append_channel_parameter(
        lines, "router1", flow_count, "per", f"{forward_per:.12g}"
    )
    lines.append("    </at>")


def append_handover_start(lines: list[str], flow_count: int, time_s: int) -> None:
    lines.append(f'    <at t="{time_s}">')
    lines.append(
        f'        <disconnect src-module="router1" src-gate="pppg$o[{flow_count}]"/>'
    )
    lines.append(
        f'        <disconnect src-module="router2" src-gate="pppg$o[{flow_count}]"/>'
    )
    lines.append(f'        <crash module="router1.ppp[{flow_count}]"/>')
    lines.append(f'        <crash module="router2.ppp[{flow_count}]"/>')
    lines.append("    </at>")


def append_connection(
    lines: list[str], source: str, destination: str, flow_count: int, state: dict,
    per: float | None = None,
) -> None:
    one_way_link_delay_ms = float(state["rtt_ms"]) / 6
    lines.append(
        f'        <connect src-module="{source}" src-gate="pppg$o[{flow_count}]"'
    )
    lines.append(
        f'                 dest-module="{destination}" dest-gate="pppg$i[{flow_count}]"'
    )
    lines.append('                 channel-type="ned.DatarateChannel">')
    lines.append(
        f'                 <param name="datarate" value="{int(state["bandwidth_mbps"])}Mbps" />'
    )
    lines.append(
        f'                 <param name="delay" value="{one_way_link_delay_ms:.12g}ms" />'
    )
    if per is not None:
        lines.append(f'                 <param name="per" value="{per:.12g}" />')
    lines.append("        </connect>")


def append_handover_end(
    lines: list[str], flow_count: int, state: dict, has_loss: bool
) -> None:
    reconnect_time_s = float(state["reconnect_time_s"])
    forward_per = float(state["loss_per"]) if has_loss else 0.0
    lines.append(f'    <at t="{reconnect_time_s:.6f}">')
    append_connection(
        lines, "router1", "router2", flow_count, state, per=forward_per
    )
    append_connection(lines, "router2", "router1", flow_count, state)
    lines.append(f'        <start module="router1.ppp[{flow_count}]"/>')
    lines.append(f'        <start module="router2.ppp[{flow_count}]"/>')
    lines.append('        <update module="configurator" />')
    append_access_path(
        lines, flow_count, float(state["rtt_ms"]) / 6, set_rate=False
    )
    lines.append("    </at>")


def write_scenario(
    output_path: Path,
    flow_count: int,
    states: list[dict],
    has_loss: bool,
) -> None:
    lines = ["<scenario>"]
    append_initial_state(lines, flow_count, states[0], has_loss)
    for state in states[1:]:
        append_handover_start(lines, flow_count, int(state["handover_time_s"]))
        append_handover_end(lines, flow_count, state, has_loss)
    lines.append("</scenario>")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    out_dir = Path("../../paperExperiments/scenarios") / EXPERIMENT
    out_dir.mkdir(parents=True, exist_ok=True)
    traces = build_traces()

    for run, states in traces.items():
        (out_dir / f"{trace_name(run)}.json").write_text(
            json.dumps(
                {
                    "run": run,
                    "simulation_time_s": SIMULATION_TIME_S,
                    "handover_interval_s": HANDOVER_INTERVAL_S,
                    "states": states,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        for flow_count in FLOW_COUNTS:
            for condition in CONDITIONS:
                path = out_dir / f"{scenario_name(flow_count, condition, run)}.xml"
                write_scenario(path, flow_count, states, condition.has_loss)

    scenario_count = len(FLOW_COUNTS) * len(CONDITIONS) * len(RUNS)
    print(
        f"Generated {scenario_count} matched scenarios and {len(RUNS)} "
        f"balanced traces for {EXPERIMENT}."
    )


if __name__ == "__main__":
    main()
