#!/usr/bin/env python3

# Generate INI files for experiment 11 for each congestion control algorithm.
# Uses scenario XMLs in ../../paperExperiments/scenarios/experiment11/{5flows,10flows,20flows}/
# Assumes scenario file is named "50ms.xml" in each batch folder.

from pathlib import Path
import random

ALG_FLAVOUR = {
    "cubic": ("TcpPaced", "TcpCubic"),
    "satcp": ("Satcp", "SatcpFlavour"),
    "bbr": ("Bbr", "BbrFlavour"),
    "bbr3": ("Bbr", "Bbr3Flavour"),
    "orbtcp": ("Orbtcp", "OrbtcpFlavour"),
    "leocc": ("Leocc", "LeoccFlavour"),
}

MSS_BYTES = 1448


def main() -> None:
    simSeed = 1999
    bandwidth_mbps = 200
    queue_bdp_multiplier = 5
    numOfRuns = 5
    batchSizes = [5, 10, 20]
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"]

    out_dir = Path("../../paperExperiments/experiment11")
    scenarios_root = Path("../../paperExperiments/scenarios/experiment11")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Shared settings
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
        f"**.tcp.mss = {MSS_BYTES}",
        "**.tcp.sackSupport = true",
    ]

    # App[0] is always the bulk sender
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
        fileName = out_dir / f"experiment11_{alg}.ini"
        print(f"\nGenerating ini file for {alg}...")

        client_num_apps = 2 if alg == "leocc" else 1

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
                "sim-time-limit = 250s",
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
                "**.**.tcp.conn-*.retransmissionRate:vector(removeRepeats).vector-recording = true",
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
                "*.configurator.optimizeRoutes = false",
                "",
            ])

            # ---------------- Algorithm block ----------------
            w(f'**.tcp.typename = "{tcp_type}"')
            w(f'**.tcp.tcpAlgorithmClass = "{alg_class}"')
            block(common_tcp)
            w()

            # Apps
            w(f"*.client[*].numApps = {client_num_apps}")
            block(common_app0)

            if alg == "leocc":
                # Leocc requires a LeoccPingApp per client
                w('*.client[*].app[1].typename = "LeoccPingApp"')
                w("*.client[*].app[1].startTime = 0s")
                w('*.client[*].app[1].destAddr = "server[" + string(parentIndex()) + "]"')
                w("*.client[*].app[1].sendInterval = 10ms")
                w("*.client[*].app[1].packetSize = 1B")

            w()

            # Queue / extra knobs + initial ssthresh
            if alg in ("cubic", "satcp"):
                w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
                w()
                w(f"**.tcp.initialSsthresh = {400 * MSS_BYTES}")
                w()

            elif alg in ("bbr", "bbr3"):
                w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
                w()
                w(f"**.tcp.initialSsthresh = {4000 * MSS_BYTES}")
                w()

            elif alg == "leocc":
                w('**.ppp[*].queue.typename = "LeoccQueue"')
                w()
                w(f"**.tcp.initialSsthresh = {4000 * MSS_BYTES}")
                w()

            else:  # orbtcp
                w('**.**.queue.typename = "DropTailQueue"')
                w()
                w("**.additiveIncreasePercent = 0.05")
                w("**.eta = 0.95")
                w("**.alpha = 0.01")
                w("**.fixedAvgRTTVal = 0")
                w()
                w(f"**.tcp.initialSsthresh = {4000 * MSS_BYTES}")
                w()

            # ---------------- Config sections ----------------
            for numFlows in batchSizes:
                batch_folder = scenarios_root / f"{numFlows}flows"
                scenario_file = batch_folder / "50ms.xml"

                if not scenario_file.exists():
                    print(f"Warning: missing scenario file {scenario_file}")
                    continue

                scenario_name = scenario_file.stem  # "50ms"
                rtt_ms = int(scenario_name.replace("ms", ""))
                rtt_s = rtt_ms / 1000.0

                # BDP in bytes = bandwidth_bytes_per_sec * RTT_seconds
                bw_bytes_per_sec = bandwidth_mbps * 125000
                bdp_bytes = bw_bytes_per_sec * rtt_s

                # 5x BDP, convert bytes -> packets (MSS=1448)
                queue_packets = int((bdp_bytes * queue_bdp_multiplier) / MSS_BYTES)

                # Even spacing over first 100s, with ±2.5s jitter
                # 5 flows -> 20s, 10 flows -> 10s, 20 flows -> 5s
                interval = 100.0 / numFlows

                for runIdx in range(numOfRuns):
                    random.seed(simSeed + runIdx + numFlows)

                    configName = f"{alg.title()}_{numFlows}flows_{scenario_name}_Run{runIdx+1}"
                    print(configName)

                    w(f"[Config {configName}]")
                    w("extends = General ")
                    w()
                    w(f"**.numberOfFlows = {numFlows}")
                    w()

                    # ORBTCP IntQueue must be on router1's bottleneck interface: ppp[numFlows]
                    if alg == "orbtcp":
                        w(f'**.router1.ppp[{numFlows}].queue.typename = "IntQueue"')
                        w()

                    for clientNumb in range(numFlows):
                        baseStart = (clientNumb + 1) * interval
                        clientStart = random.uniform(baseStart - 2.5, baseStart + 2.5)
                        if clientStart < 0:
                            clientStart = 0.01

                        # client[i] connects to server[i]
                        w(f'*.client[{clientNumb}].app[0].connectAddress = "server[{clientNumb}]"')
                        w(f"*.client[{clientNumb}].app[0].tOpen = {clientStart}s")
                        w(f"*.client[{clientNumb}].app[0].tSend = {clientStart}s")
                        w()

                    w(f"**.ppp[*].queue.packetCapacity = {queue_packets}")
                    w()

                    scenario_doc = f'xmldoc("../scenarios/experiment11/{numFlows}flows/{scenario_name}.xml")'
                    w(f"*.scenarioManager.script = {scenario_doc}")
                    if alg == "satcp":
                        w(f"**.tcp.scenario = {scenario_doc}")
                    w()

    print("\nINI files generated!")


if __name__ == "__main__":
    main()