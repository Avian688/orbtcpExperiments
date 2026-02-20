#!/usr/bin/env python3

# Generates scenario XML files for experiment 1.
# Hard handover every 5s: disconnect+crash, then reconnect after random 45–120ms.
# RTT is equally spread across ALL THREE links:
#   client<->router1 (pppg$o[0]), router1<->router2 (pppg$o[1]), router2<->server (pppg$o[0])
# So each link one-way delay = RTT/6.
# Access links are fixed 10Gbps; bottleneck BW changes.
# Keeps loss-rate RNG draw (currentPer) to keep random sequence consistent.

import json
import random
from pathlib import Path


def main() -> None:
    minBw = 50   # Mbps
    maxBw = 100  # Mbps
    minRtt = 1   # ms
    maxRtt = 100 # ms

    numOfRuns = 50
    simLength = 300     # seconds
    simSeed = 1

    handoverEvery = 5       # seconds
    minHandoverMs = 45      # ms
    maxHandoverMs = 120     # ms

    fixed_access_bw = "10Gbps"

    folderScenario = Path("../../paperExperiments/scenarios/experiment1/")
    folderBaseRtts = Path("../../paperExperiments/baseRtts/experiment1/")
    folderBws = Path("../../paperExperiments/bandwidths/experiment1/")
    folderScenario.mkdir(parents=True, exist_ok=True)
    folderBaseRtts.mkdir(parents=True, exist_ok=True)
    folderBws.mkdir(parents=True, exist_ok=True)

    for run_idx in range(numOfRuns):
        rng = random.Random(simSeed + run_idx)

        baseRttDict = {}
        bwDict = {}

        fileName = f"run{run_idx + 1}"
        xml_path = folderScenario / f"{fileName}.xml"

        with xml_path.open("w", encoding="utf-8") as f:
            def w(line: str = "") -> None:
                f.write(line + "\n")

            def block(lines) -> None:
                for line in lines:
                    w(line)

            w("<scenario>")

            # ---- Initial conditions at t=0 ----
            currentBw = rng.randint(minBw, maxBw)     # Mbps
            currentRtt = rng.randint(minRtt, maxRtt)  # ms
            currentPer = round(rng.uniform(0, 0.01), 4)  # keep RNG consistency (unused here)

            # Equal spread across 3 links:
            # RTT = 2 * (d + d + d) = 6d => d = RTT/6 (one-way per link)
            linkDelay = currentRtt / 6.0

            w('    <at t="0">')
            block([
                # ---- Set equal per-link one-way delays ----
                f'        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                f'        <set-channel-param src-module="router1"   src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                "",
                f'        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="delay" value="{linkDelay}ms"/>',
                f'        <set-channel-param src-module="router2" src-gate="pppg$o[1]" par="delay" value="{linkDelay}ms"/>',
                "",
                f'        <set-channel-param src-module="router2"   src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                f'        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                "",
                # ---- Access links fixed 10Gbps ----
                f'        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="datarate" value="{fixed_access_bw}"/>',
                f'        <set-channel-param src-module="router1"   src-gate="pppg$o[0]" par="datarate" value="{fixed_access_bw}"/>',
                f'        <set-channel-param src-module="router2"   src-gate="pppg$o[0]" par="datarate" value="{fixed_access_bw}"/>',
                f'        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="datarate" value="{fixed_access_bw}"/>',
                "",
                # ---- Bottleneck BW at t=0 ----
                f'        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="datarate" value="{currentBw}Mbps"/>',
                f'        <set-channel-param src-module="router2" src-gate="pppg$o[1]" par="datarate" value="{currentBw}Mbps"/>',
            ])
            w("    </at>")

            baseRttDict["0"] = currentRtt
            bwDict["0"] = currentBw

            # ---- Handover loop: every 5 seconds ----
            t = handoverEvery
            while t <= simLength:
                dur_ms = rng.randint(minHandoverMs, maxHandoverMs)
                dur_s = dur_ms / 1000.0
                reconnect_t = t + dur_s

                # Start hard handover: disconnect + crash bottleneck PPPs
                w(f'    <at t="{t}">')
                block([
                    '        <disconnect src-module="router1" src-gate="pppg$o[1]"/>',
                    '        <disconnect src-module="router2" src-gate="pppg$o[1]"/>',
                    '        <crash module="router1.ppp[1]"/>',
                    '        <crash module="router2.ppp[1]"/>',
                ])
                w("    </at>")

                # New conditions apply AFTER handover
                currentBw = rng.randint(minBw, maxBw)
                currentRtt = rng.randint(minRtt, maxRtt)
                currentPer = round(rng.uniform(0, 0.01), 4)  # keep RNG sequence consistent

                linkDelay = currentRtt / 6.0

                # Reconnect bottleneck with NEW BW and NEW bottleneck delay
                w(f'    <at t="{reconnect_t}">')
                block([
                    '        <connect src-module="router1" src-gate="pppg$o[1]"',
                    '                 dest-module="router2" dest-gate="pppg$i[1]"',
                    '                 channel-type="ned.DatarateChannel">',
                    f'                 <param name="datarate" value="{currentBw}Mbps" />',
                    f'                 <param name="delay" value="{linkDelay}ms" />',
                    "        </connect>",
                    '        <connect src-module="router2" src-gate="pppg$o[1]"',
                    '                 dest-module="router1" dest-gate="pppg$i[1]"',
                    '                 channel-type="ned.DatarateChannel">',
                    f'                 <param name="datarate" value="{currentBw}Mbps" />',
                    f'                 <param name="delay" value="{linkDelay}ms" />',
                    "        </connect>",
                    '        <start module="router1.ppp[1]"/>',
                    '        <start module="router2.ppp[1]"/>',
                    '        <update module="configurator" />',
                    "",
                    # Update the other two links' delays to keep equal spread
                    f'        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                    f'        <set-channel-param src-module="router1"   src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                    "",
                    f'        <set-channel-param src-module="router2"   src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                    f'        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="delay" value="{linkDelay}ms"/>',
                ])
                w("    </at>")

                baseRttDict[f"{reconnect_t}"] = currentRtt
                bwDict[f"{reconnect_t}"] = currentBw

                t += handoverEvery

            w("</scenario>")

        (folderBaseRtts / f"{fileName}.json").write_text(json.dumps(baseRttDict, indent=2), encoding="utf-8")
        (folderBws / f"{fileName}.json").write_text(json.dumps(bwDict, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()