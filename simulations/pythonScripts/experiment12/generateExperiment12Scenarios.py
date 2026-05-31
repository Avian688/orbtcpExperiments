#!/usr/bin/env python3

from pathlib import Path
import random


BOTTLENECK_INTERFACE = 1
BOTTLENECK_DELAY_MS = 0.5
BOTTLENECK_DATARATE = "100Mbps"
RECONFIGURATION_TIMES = list(range(15, 100, 15))
MIN_DOWNTIME_MS = 45
MAX_DOWNTIME_MS = 120


def main() -> None:
    rng = random.Random(12)
    out_dir = Path("../../paperExperiments/scenarios/experiment12")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "reconfigurations.xml"

    lines = ["<scenario>"]
    for reconfiguration_time in RECONFIGURATION_TIMES:
        downtime_ms = rng.randint(MIN_DOWNTIME_MS, MAX_DOWNTIME_MS)
        reconnect_time = reconfiguration_time + downtime_ms / 1000.0

        lines.extend(
            [
                f'    <at t="{reconfiguration_time}">',
                f'        <disconnect src-module="router1" src-gate="pppg$o[{BOTTLENECK_INTERFACE}]"/>',
                f'        <disconnect src-module="router2" src-gate="pppg$o[{BOTTLENECK_INTERFACE}]"/>',
                f'        <crash module="router1.ppp[{BOTTLENECK_INTERFACE}]"/>',
                f'        <crash module="router2.ppp[{BOTTLENECK_INTERFACE}]"/>',
                "    </at>",
                f'    <at t="{reconnect_time}">',
                f'        <connect src-module="router1" src-gate="pppg$o[{BOTTLENECK_INTERFACE}]"',
                f'                 dest-module="router2" dest-gate="pppg$i[{BOTTLENECK_INTERFACE}]"',
                '                 channel-type="ned.DatarateChannel">',
                f'                 <param name="datarate" value="{BOTTLENECK_DATARATE}" />',
                f'                 <param name="delay" value="{BOTTLENECK_DELAY_MS}ms" />',
                "        </connect>",
                f'        <connect src-module="router2" src-gate="pppg$o[{BOTTLENECK_INTERFACE}]"',
                f'                 dest-module="router1" dest-gate="pppg$i[{BOTTLENECK_INTERFACE}]"',
                '                 channel-type="ned.DatarateChannel">',
                f'                 <param name="datarate" value="{BOTTLENECK_DATARATE}" />',
                f'                 <param name="delay" value="{BOTTLENECK_DELAY_MS}ms" />',
                "        </connect>",
                f'        <start module="router1.ppp[{BOTTLENECK_INTERFACE}]"/>',
                f'        <start module="router2.ppp[{BOTTLENECK_INTERFACE}]"/>',
                '        <update module="configurator" />',
                "    </at>",
            ]
        )

    lines.append("</scenario>")
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {out_file} with {len(RECONFIGURATION_TIMES)} reconfigurations.")


if __name__ == "__main__":
    main()
