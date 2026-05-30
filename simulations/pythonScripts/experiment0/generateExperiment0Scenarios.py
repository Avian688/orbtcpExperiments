#!/usr/bin/env python3

import json
import random
from pathlib import Path


BASE_BW_MBPS = 100
BASE_RTT_MS = 50
SIM_TIME_LIMIT_S = 120
RUNS = 5
START_TIME_SEED = 0


def per_link_delay_ms(rtt_ms: float) -> float:
    return rtt_ms / 6.0


def write_delay_updates(write, rtt_ms: float) -> None:
    delay = per_link_delay_ms(rtt_ms)
    for module, gate in (
        ("client[0]", 0),
        ("router1", 0),
        ("router1", 1),
        ("router2", 1),
        ("router2", 0),
        ("server[0]", 0),
    ):
        write(
            f'        <set-channel-param src-module="{module}" src-gate="pppg$o[{gate}]" '
            f'par="delay" value="{delay:.6f}ms"/>'
        )


def write_bottleneck_bw(write, bw_mbps: int) -> None:
    for module in ("router1", "router2"):
        write(
            f'        <set-channel-param src-module="{module}" src-gate="pppg$o[1]" '
            f'par="datarate" value="{bw_mbps}Mbps"/>'
        )


def write_bottleneck_loss(write, per: float) -> None:
    for module in ("router1", "router2"):
        write(
            f'        <set-channel-param src-module="{module}" src-gate="pppg$o[1]" '
            f'par="per" value="{per}"/>'
        )


def main() -> None:
    scenario_dir = Path("../../paperExperiments/scenarios/experiment0")
    start_time_dir = Path("../../paperExperiments/startTimes/experiment0")
    scenario_dir.mkdir(parents=True, exist_ok=True)
    start_time_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(START_TIME_SEED)
    start_times = {
        f"run{run}": round(rng.uniform(0.0, 0.1), 6)
        for run in range(1, RUNS + 1)
    }
    (start_time_dir / "start_times.json").write_text(json.dumps(start_times, indent=2), encoding="utf-8")

    for run in range(1, RUNS + 1):
        xml_path = scenario_dir / f"run{run}.xml"
        with xml_path.open("w", encoding="utf-8") as f:
            def w(line: str = "") -> None:
                f.write(line + "\n")

            w("<scenario>")

            w('    <at t="15">')
            write_bottleneck_bw(w, BASE_BW_MBPS * 2)
            w("    </at>")

            w('    <at t="30">')
            write_bottleneck_bw(w, BASE_BW_MBPS)
            w("    </at>")

            w('    <at t="35">')
            write_delay_updates(w, BASE_RTT_MS * 2)
            w("    </at>")

            w('    <at t="60">')
            write_delay_updates(w, BASE_RTT_MS)
            w("    </at>")

            w('    <at t="75">')
            write_bottleneck_loss(w, 0.01)
            w("    </at>")

            w('    <at t="90">')
            write_bottleneck_loss(w, 0)
            w("    </at>")

            w("</scenario>")

    metadata = {
        "runs": RUNS,
        "base_bw_mbps": BASE_BW_MBPS,
        "base_rtt_ms": BASE_RTT_MS,
        "sim_time_limit_s": SIM_TIME_LIMIT_S,
        "events": [
            {"time_s": 15, "action": "double bandwidth", "bw_mbps": 200},
            {"time_s": 30, "action": "halve bandwidth", "bw_mbps": 100},
            {"time_s": 35, "action": "double RTT", "rtt_ms": 100},
            {"time_s": 60, "action": "halve RTT", "rtt_ms": 50},
            {"time_s": 75, "action": "add bottleneck packet loss", "per": 0.01},
            {"time_s": 90, "action": "remove bottleneck packet loss", "per": 0},
        ],
    }
    (start_time_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
