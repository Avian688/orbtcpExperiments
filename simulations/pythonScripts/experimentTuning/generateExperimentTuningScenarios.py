#!/usr/bin/env python3

from __future__ import annotations

import json
import random
from pathlib import Path

from experimentTuningSupport import (
    BANDWIDTH_MBPS,
    EXPERIMENT,
    FLOW_COUNTS,
    HANDOVER_INTERVAL_S,
    MAX_HANDOVER_DOWNTIME_MS,
    MIN_HANDOVER_DOWNTIME_MS,
    RTT_MS,
    RUNS,
    SIMULATION_TIME_S,
    scenario_name,
)


BOTTLENECK_DELAY_MS = 0.5
ACCESS_RATE = "10Gbps"


def write_initial_path(lines: list[str], flow_count: int) -> None:
    access_delay_ms = (RTT_MS - 2 * BOTTLENECK_DELAY_MS) / 4
    lines.append('    <at t="0">')

    for index in range(flow_count):
        for module, gate in (
            (f"client[{index}]", 0),
            ("router1", index),
            (f"server[{index}]", 0),
            ("router2", index),
        ):
            lines.append(
                f'        <set-channel-param src-module="{module}" '
                f'src-gate="pppg$o[{gate}]" par="delay" value="{access_delay_ms}ms"/>'
            )
            lines.append(
                f'        <set-channel-param src-module="{module}" '
                f'src-gate="pppg$o[{gate}]" par="datarate" value="{ACCESS_RATE}"/>'
            )

    for module in ("router1", "router2"):
        lines.append(
            f'        <set-channel-param src-module="{module}" '
            f'src-gate="pppg$o[{flow_count}]" par="delay" '
            f'value="{BOTTLENECK_DELAY_MS}ms"/>'
        )
        lines.append(
            f'        <set-channel-param src-module="{module}" '
            f'src-gate="pppg$o[{flow_count}]" par="datarate" '
            f'value="{BANDWIDTH_MBPS}Mbps"/>'
        )
    lines.append("    </at>")


def write_handover_start(lines: list[str], flow_count: int, time_s: int) -> None:
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


def write_handover_end(
    lines: list[str], flow_count: int, reconnect_time_s: float
) -> None:
    lines.append(f'    <at t="{reconnect_time_s:.6f}">')
    lines.append(
        f'        <connect src-module="router1" src-gate="pppg$o[{flow_count}]"'
    )
    lines.append(
        f'                 dest-module="router2" dest-gate="pppg$i[{flow_count}]"'
    )
    lines.append('                 channel-type="ned.DatarateChannel">')
    lines.append(
        f'                 <param name="datarate" value="{BANDWIDTH_MBPS}Mbps" />'
    )
    lines.append(
        f'                 <param name="delay" value="{BOTTLENECK_DELAY_MS}ms" />'
    )
    lines.append("        </connect>")
    lines.append(
        f'        <connect src-module="router2" src-gate="pppg$o[{flow_count}]"'
    )
    lines.append(
        f'                 dest-module="router1" dest-gate="pppg$i[{flow_count}]"'
    )
    lines.append('                 channel-type="ned.DatarateChannel">')
    lines.append(
        f'                 <param name="datarate" value="{BANDWIDTH_MBPS}Mbps" />'
    )
    lines.append(
        f'                 <param name="delay" value="{BOTTLENECK_DELAY_MS}ms" />'
    )
    lines.append("        </connect>")
    lines.append(f'        <start module="router1.ppp[{flow_count}]"/>')
    lines.append(f'        <start module="router2.ppp[{flow_count}]"/>')
    lines.append('        <update module="configurator" />')
    lines.append("    </at>")


def generate_scenario(flow_count: int, run: int, out_dir: Path) -> None:
    # Reinitializing from run alone makes each run's downtime trace identical
    # for 5, 20, and 100 flows, while all protocol variants share the same XML.
    rng = random.Random(17_000 + run)
    lines = ["<scenario>"]
    events = []
    write_initial_path(lines, flow_count)

    for handover_time_s in range(
        HANDOVER_INTERVAL_S, SIMULATION_TIME_S, HANDOVER_INTERVAL_S
    ):
        downtime_ms = rng.randint(
            MIN_HANDOVER_DOWNTIME_MS, MAX_HANDOVER_DOWNTIME_MS
        )
        reconnect_time_s = handover_time_s + downtime_ms / 1000
        write_handover_start(lines, flow_count, handover_time_s)
        write_handover_end(lines, flow_count, reconnect_time_s)
        events.append(
            {
                "disconnect_time_s": handover_time_s,
                "reconnect_time_s": reconnect_time_s,
                "downtime_ms": downtime_ms,
            }
        )

    lines.append("</scenario>")
    stem = scenario_name(flow_count, run)
    (out_dir / f"{stem}.xml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    (out_dir / f"{stem}.json").write_text(
        json.dumps(
            {
                "flow_count": flow_count,
                "run": run,
                "rtt_ms": RTT_MS,
                "bandwidth_mbps": BANDWIDTH_MBPS,
                "handover_events": events,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    out_dir = Path("../../paperExperiments/scenarios") / EXPERIMENT
    out_dir.mkdir(parents=True, exist_ok=True)
    for flow_count in FLOW_COUNTS:
        for run in RUNS:
            generate_scenario(flow_count, run, out_dir)
    count = len(FLOW_COUNTS) * len(RUNS)
    print(f"Generated {count} matched {EXPERIMENT} handover scenarios in {out_dir}.")


if __name__ == "__main__":
    main()
