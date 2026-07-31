#!/usr/bin/env python3

from __future__ import annotations

import json
import random
from pathlib import Path

from experiment13Support import HANDOVER_INTERVAL_S, RUNS, SIMULATION_TIME_S, WORKLOADS, scenario_name


MIN_BANDWIDTH_MBPS = 50
MAX_BANDWIDTH_MBPS = 100
MIN_RTT_MS = 1
MAX_RTT_MS = 100
MIN_DOWNTIME_MS = 45
MAX_DOWNTIME_MS = 120
ACCESS_BANDWIDTH = "10Gbps"


def write(lines: list[str], line: str = "") -> None:
    lines.append(line)


def write_initial_pathchange(lines: list[str], bandwidth_mbps: int, rtt_ms: int) -> None:
    link_delay_ms = rtt_ms / 6.0
    write(lines, '    <at t="0">')
    for module, gate in (("client", 0), ("router1", 0), ("router2", 0), ("server", 0)):
        write(lines, f'        <set-channel-param src-module="{module}" src-gate="pppg$o[{gate}]" par="delay" value="{link_delay_ms}ms"/>')
        write(lines, f'        <set-channel-param src-module="{module}" src-gate="pppg$o[{gate}]" par="datarate" value="{ACCESS_BANDWIDTH}"/>')
    for module in ("router1", "router2"):
        write(lines, f'        <set-channel-param src-module="{module}" src-gate="pppg$o[1]" par="delay" value="{link_delay_ms}ms"/>')
        write(lines, f'        <set-channel-param src-module="{module}" src-gate="pppg$o[1]" par="datarate" value="{bandwidth_mbps}Mbps"/>')
    write(lines, "    </at>")


def write_handover_start(lines: list[str], time_s: int) -> None:
    write(lines, f'    <at t="{time_s}">')
    write(lines, '        <disconnect src-module="router1" src-gate="pppg$o[1]"/>')
    write(lines, '        <disconnect src-module="router2" src-gate="pppg$o[1]"/>')
    write(lines, '        <crash module="router1.ppp[1]"/>')
    write(lines, '        <crash module="router2.ppp[1]"/>')
    write(lines, "    </at>")


def write_reconnect(
    lines: list[str],
    reconnect_time_s: float,
    bandwidth_mbps: int,
    rtt_ms: int,
) -> None:
    link_delay_ms = rtt_ms / 6.0
    write(lines, f'    <at t="{reconnect_time_s}">')
    write(lines, '        <connect src-module="router1" src-gate="pppg$o[1]"')
    write(lines, '                 dest-module="router2" dest-gate="pppg$i[1]"')
    write(lines, '                 channel-type="ned.DatarateChannel">')
    write(lines, f'                 <param name="datarate" value="{bandwidth_mbps}Mbps" />')
    write(lines, f'                 <param name="delay" value="{link_delay_ms}ms" />')
    write(lines, "        </connect>")
    write(lines, '        <connect src-module="router2" src-gate="pppg$o[1]"')
    write(lines, '                 dest-module="router1" dest-gate="pppg$i[1]"')
    write(lines, '                 channel-type="ned.DatarateChannel">')
    write(lines, f'                 <param name="datarate" value="{bandwidth_mbps}Mbps" />')
    write(lines, f'                 <param name="delay" value="{link_delay_ms}ms" />')
    write(lines, "        </connect>")
    write(lines, '        <start module="router1.ppp[1]"/>')
    write(lines, '        <start module="router2.ppp[1]"/>')
    write(lines, '        <update module="configurator" />')

    for module, gate in (("client", 0), ("router1", 0), ("router2", 0), ("server", 0)):
        write(lines, f'        <set-channel-param src-module="{module}" src-gate="pppg$o[{gate}]" par="delay" value="{link_delay_ms}ms"/>')
    write(lines, "    </at>")


def generate_workload(workload: str, run: int, out_dir: Path) -> None:
    # The same trace is shared by full INT and every PINT probability for this run.
    rng = random.Random(1300 + run * 17)
    lines = ["<scenario>"]
    events = []

    bandwidth_mbps = rng.randint(MIN_BANDWIDTH_MBPS, MAX_BANDWIDTH_MBPS)
    rtt_ms = rng.randint(MIN_RTT_MS, MAX_RTT_MS)
    write_initial_pathchange(lines, bandwidth_mbps, rtt_ms)
    events.append({"time_s": 0.0, "bandwidth_mbps": bandwidth_mbps, "rtt_ms": rtt_ms})

    for handover_time_s in range(HANDOVER_INTERVAL_S, SIMULATION_TIME_S, HANDOVER_INTERVAL_S):
        write_handover_start(lines, handover_time_s)
        downtime_ms = rng.randint(MIN_DOWNTIME_MS, MAX_DOWNTIME_MS)
        reconnect_time_s = handover_time_s + downtime_ms / 1000.0
        bandwidth_mbps = rng.randint(MIN_BANDWIDTH_MBPS, MAX_BANDWIDTH_MBPS)
        rtt_ms = rng.randint(MIN_RTT_MS, MAX_RTT_MS)
        write_reconnect(lines, reconnect_time_s, bandwidth_mbps, rtt_ms)
        events.append({
            "time_s": reconnect_time_s,
            "bandwidth_mbps": bandwidth_mbps,
            "rtt_ms": rtt_ms,
        })

    lines.append("</scenario>")
    stem = scenario_name(workload, run)
    (out_dir / f"{stem}.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.json").write_text(
        json.dumps({"workload": workload, "run": run, "events": events}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    out_dir = Path("../../paperExperiments/scenarios/experiment13")
    out_dir.mkdir(parents=True, exist_ok=True)
    for workload in WORKLOADS:
        for run in RUNS:
            generate_workload(workload, run, out_dir)
    print(f"Generated {len(WORKLOADS) * len(RUNS)} matched Experiment 13 scenario traces in {out_dir}.")


if __name__ == "__main__":
    main()
