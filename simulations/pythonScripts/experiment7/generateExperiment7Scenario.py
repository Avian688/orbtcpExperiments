#!/usr/bin/env python3

# Generates path disruption scenario XML files for scenario manager.
# For each RTT and disruption interval, it periodically disconnects the router1<->router2 link,
# crashes the PPP modules, then reconnects after disruptionInterval (ms).

from pathlib import Path
import random


def main() -> None:
    simLength = 300
    intervalLength = 5
    simSeed = 1

    rtts = [50]
    disruptionIntervals = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]  # ms

    out_dir = Path("../../paperExperiments/scenarios/experiment7")
    out_dir.mkdir(parents=True, exist_ok=True)

    random.seed(simSeed)

    for rtt in rtts:
        for disruptionInterval in disruptionIntervals:
            fileName = f"RTT{rtt}ms_Disruption{disruptionInterval}ms"
            out_path = out_dir / f"{fileName}.xml"

            with out_path.open("w", encoding="utf-8") as f:
                def w(line: str = "") -> None:
                    f.write(line + "\n")

                def block(lines) -> None:
                    for line in lines:
                        w(line)

                w("<scenario>")

                # Your original formula: RTT includes a fixed 0.5ms delay on two directions,
                # split across 4 segments.
                channelDelay = (rtt - (0.5 * 2)) / 4

                currentInterval = 0
                while currentInterval <= simLength:
                    if currentInterval == 0:
                        w(f'    <at t="{currentInterval}">')
                        block([
                            f'        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="delay" value="{channelDelay}ms"/>',
                            f'        <set-channel-param src-module="router1" src-gate="pppg$o[0]" par="delay" value="{channelDelay}ms"/>',
                            "",
                            f'        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="delay" value="{channelDelay}ms"/>',
                            f'        <set-channel-param src-module="router2" src-gate="pppg$o[0]" par="delay" value="{channelDelay}ms"/>',
                            "",
                            '        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="datarate" value="100Mbps"/>',
                            '        <set-channel-param src-module="router2" src-gate="pppg$o[1]" par="datarate" value="100Mbps"/>',
                        ])
                        w("    </at>")
                    else:
                        # Disconnect + crash the inter-router PPP interface
                        w(f'    <at t="{currentInterval}">')
                        block([
                            '        <disconnect src-module="router1" src-gate="pppg$o[1]"/>',
                            '        <disconnect src-module="router2" src-gate="pppg$o[1]"/>',
                            '        <crash module="router1.ppp[1]"/>',
                            '        <crash module="router2.ppp[1]"/>',
                            # '        <update module="configurator" />',
                        ])
                        w("    </at>")

                        # Reconnect after disruptionInterval (ms -> seconds)
                        reconnect_t = currentInterval + (disruptionInterval / 1000)
                        w(f'    <at t="{reconnect_t}">')
                        block([
                            '        <connect src-module="router1" src-gate="pppg$o[1]"',
                            '                 dest-module="router2" dest-gate="pppg$i[1]"',
                            '                 channel-type="ned.DatarateChannel">',
                            '                 <param name="datarate" value="100Mbps" />',
                            '                 <param name="delay" value="0.5ms" />',
                            "        </connect>",
                            '        <connect src-module="router2" src-gate="pppg$o[1]"',
                            '                 dest-module="router1" dest-gate="pppg$i[1]"',
                            '                 channel-type="ned.DatarateChannel">',
                            '                 <param name="datarate" value="100Mbps" />',
                            '                 <param name="delay" value="0.5ms" />',
                            "        </connect>",
                            '        <start module="router1.ppp[1]"/>',
                            '        <start module="router2.ppp[1]"/>',
                            '        <update module="configurator" />',
                        ])
                        w("    </at>")

                    currentInterval += intervalLength

                w("</scenario>")


if __name__ == "__main__":
    main()