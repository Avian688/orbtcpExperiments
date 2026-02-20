#!/usr/bin/env python3

# Generates INI files for experiment 7 for each congestion control algorithm.
# Writes [General], algorithm-specific TCP settings, then one [Config] per scenario XML and per run.

import math
import random
import re
from pathlib import Path

ALG_FLAVOUR = {
    "cubic": ("TcpPaced", "TcpCubic"),
    "satcp": ("Satcp", "SatcpFlavour"),        # Satcp is the main TCP protocol
    "bbr": ("Bbr", "BbrFlavour"),
    "bbr3": ("Bbr", "Bbr3Flavour"),
    "orbtcp": ("Orbtcp", "OrbtcpFlavour"),
    "leocc": ("Leocc", "LeoccFlavour"),        # like BBR, but with LeoccQueue everywhere
}


def main() -> None:
    simSeed = 1999
    queueSizes = [1]  # [0.2, 1, 4]
    bandwidth = 12500000
    numOfRuns = 5

    algorithms = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"]

    out_dir = Path("../../paperExperiments/experiment7")
    scenarios_dir = Path("../../paperExperiments/scenarios/experiment7")
    out_dir.mkdir(parents=True, exist_ok=True)

    scenario_files = sorted(scenarios_dir.iterdir())

    common_tcp = [
        "**.tcp.advertisedWindow = 200000000",
        "**.tcp.windowScalingSupport = true",
        "**.tcp.windowScalingFactor = -1",
        "**.tcp.increasedIWEnabled = true",
        "**.tcp.delayedAcksEnabled = false",
        "**.tcp.timestampSupport = true",
        "**.tcp.ecnWillingness = false",
        "**.tcp.nagleEnabled = true",
        "**.tcp.stopOperationTimeout = 4000s",
        "**.tcp.mss = 1448",
        "**.tcp.sackSupport = true",
    ]

    # App[0] is always the bulk sender in this experiment
    common_app0 = [
        '*.client[*].app[0].typename  = "TcpGoodputSessionApp"',
        "*.client[*].app[0].tClose = -1s",
        "*.client[*].app[0].sendBytes = 2GB",
        '*.client[*].app[0].dataTransferMode = "bytecount"',
        "*.client[*].app[0].statistic-recording = true",
        "",
        "**.server[*].numApps = 1",
        '**.server[*].app[0].typename  = "TcpSinkApp"',
        '**.server[*].app[0].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"',
    ]

    for alg in algorithms:
        tcp_type, alg_class = ALG_FLAVOUR[alg]

        # Correct numApps per algorithm
        client_num_apps = 2 if alg == "leocc" else 1

        for qs in queueSizes:
            if qs == 0.2:
                queueIniTitle = "smallbuffer"
            elif qs == 1:
                queueIniTitle = "mediumbuffer"
            elif qs == 4:
                queueIniTitle = "largebuffer"
            else:
                queueIniTitle = f"buffer{qs}"

            fileName = out_dir / f"experiment7_{alg}_{queueIniTitle}.ini"
            print(f"\nGenerating ini files for {alg}...")

            with fileName.open("w", encoding="utf-8") as f:
                def w(line: str = "") -> None:
                    f.write(line + "\n")

                def block(lines) -> None:
                    for line in lines:
                        w(line)

                # ---------------- [General] ----------------
                w("[General]")
                w()
                block([
                    "network = singledumbbell",
                    "sim-time-limit = 300s",
                    "record-eventlog=false",
                    "cmdenv-express-mode = true",
                    "cmdenv-redirect-output = false",
                    "cmdenv-output-file = dctcpLog.txt",
                    "**.client*.tcp.conn-8.cmdenv-log-level = detail",
                    "cmdenv-log-prefix = %t | %m |",
                    "",
                    "cmdenv-event-banners = false",
                    "**.cmdenv-log-level = off",
                    "",
                    "**.**.tcp.conn-*.cwnd:vector(removeRepeats).vector-recording = true",
                    "**.**.tcp.conn-*.rtt:vector(removeRepeats).vector-recording = true",
                    "**.**.tcp.conn-*.srtt:vector(removeRepeats).vector-recording = true",
                    "**.**.tcp.conn-*.throughput:vector(removeRepeats).vector-recording = true",
                    "**.**.tcp.conn-*.**.result-recording-modes = vector(removeRepeats)",
                    "",
                    "**.**.queue.queueLength:vector(removeRepeats).vector-recording = true",
                    "**.**.queue.queueLength.result-recording-modes = vector(removeRepeats)",
                    "",
                    "**.**.goodput:vector(removeRepeats).vector-recording = true",
                    "**.**.goodput.result-recording-modes = vector(removeRepeats)",
                    "",
                    "**.**.bandwidth:vector(removeRepeats).vector-recording = true",
                    "**.**.bandwidth.result-recording-modes = vector(removeRepeats)",
                    "",
                    "**.**.mbytesInFlight:vector(removeRepeats).vector-recording = true",
                    "**.**.mbytesInFlight.result-recording-modes = vector(removeRepeats)",
                    "",
                    "**.scalar-recording=false",
                    "**.vector-recording=false",
                    "**.bin-recording=false",
                    "",
                    "**.goodputInterval = 1s",
                    "**.throughputInterval = 1s",
                    "",
                ])

                # ---------------- Algorithm block ----------------
                w(f'**.tcp.typename = "{tcp_type}"')
                w(f'**.tcp.tcpAlgorithmClass = "{alg_class}"')
                block(common_tcp)
                w()

                # Apps: correct numApps + correct indices
                w(f"*.client[*].numApps = {client_num_apps}")
                block(common_app0)

                if alg == "leocc":
                    w('*.client[*].app[1].typename = "LeoccPingApp"')
                    w("*.client[*].app[1].startTime = 0s")
                    w('*.client[*].app[1].destAddr = "server[0]"')
                    w("*.client[*].app[1].sendInterval = 10ms")
                    w("*.client[*].app[1].packetSize = 1B")

                w()

                # Queue + extra knobs + initial ssthresh (same as your original behavior)
                if alg in ("cubic", "satcp"):
                    w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
                    w()
                    w(f"**.tcp.initialSsthresh = {400 * 1448}")
                    w()

                elif alg in ("bbr", "bbr3"):
                    w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
                    w()
                    w(f"**.tcp.initialSsthresh = {4000 * 1448}")
                    w()

                elif alg == "leocc":
                    w('**.ppp[*].queue.typename = "LeoccQueue"')
                    w()
                    w(f"**.tcp.initialSsthresh = {4000 * 1448}")
                    w()

                else:  # orbtcp
                    w('**.router1.ppp[1].queue.typename = "IntQueue"')
                    w('**.**.queue.typename = "DropTailQueue"')
                    w()
                    w("**.additiveIncreasePercent = 0.05")
                    w("**.eta = 0.95")
                    w("**.alpha = 0.01")
                    w("**.fixedAvgRTTVal = 0")
                    w()
                    w(f"**.tcp.initialSsthresh = {4000 * 1448}")
                    w()

                # ---------------- Config sections ----------------
                for xmlFile in scenario_files:
                    if not xmlFile.is_file() or xmlFile.suffix != ".xml":
                        continue

                    runName = xmlFile.stem
                    for i in range(numOfRuns):
                        random.seed(simSeed + i)

                        rtt = int(re.search(r"RTT(\d+)ms", runName).group(1))

                        configName = f"{alg.title()}_{queueIniTitle}_{runName}"
                        clientStart = random.uniform(0, 0.5)

                        w(f"[Config {configName}_Run{i+1}]")
                        w("extends = General ")
                        w()
                        w("**.numberOfFlows = 1 ")
                        w()
                        w('*.client[0].app[0].connectAddress = "server[0]"')
                        w(f"*.client[0].app[0].tOpen  = {clientStart}s")
                        w(f"*.client[0].app[0].tSend = {clientStart}s")
                        w()

                        pkt_cap = math.ceil((((rtt / 1000) * bandwidth) / 1448) * qs)
                        w(f"**.ppp[*].queue.packetCapacity = {pkt_cap}")
                        w()

                        scenario_doc = f'xmldoc("../scenarios/experiment7/{runName}.xml")'
                        w(f"*.scenarioManager.script = {scenario_doc}")
                        if alg == "satcp":
                            w(f"**.tcp.scenario = {scenario_doc}")
                        w()

    print("\nINI files generated!")


if __name__ == "__main__":
    main()