#!/usr/bin/env python3

# Generate INI files for experiment 1 for each congestion control algorithm.
# Uses scenario XMLs in ../../paperExperiments/scenarios/experiment1/

from pathlib import Path

ALG_FLAVOUR = {
    "cubic": ("TcpPaced", "TcpCubic"),
    "satcp": ("Satcp", "SatcpFlavour"),
    "bbr": ("Bbr", "BbrFlavour"),
    "bbr3": ("Bbr", "Bbr3Flavour"),
    "orbtcp": ("Orbtcp", "OrbtcpFlavour"),
    "leocc": ("Leocc", "LeoccFlavour"),
}


def main() -> None:
    queueLength = 340  # Average BDP
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"]

    out_dir = Path("../../paperExperiments/experiment1")
    scenarios_dir = Path("../../paperExperiments/scenarios/experiment1")
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
        fileName = out_dir / f"experiment1_{alg}.ini"
        print(f"\nGenerating ini files for {alg}...")

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

            # Apps
            w(f"*.client[*].numApps = {client_num_apps}")
            block(common_app0)

            if alg == "leocc":
                w('*.client[*].app[1].typename = "LeoccPingApp"')
                w("*.client[*].app[1].startTime = 0s")
                w('*.client[*].app[1].destAddr = "server[0]"')
                w("*.client[*].app[1].sendInterval = 10ms")
                w("*.client[*].app[1].packetSize = 1B")

            w()

            # Queue / extra knobs + initial ssthresh
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
                name = xmlFile.name
                if not (name.startswith("run") and name.endswith(".xml")):
                    continue

                runNum = int(name[3:-4])
                configName = f"{alg.title()}_Run{runNum}"

                w(f"[Config {configName}]")
                w("extends = General ")
                w()
                w("**.numberOfFlows = 1 ")
                w()
                w('*.client[0].app[0].connectAddress = "server[0]"')
                w("*.client[0].app[0].tOpen = 0s")
                w("*.client[0].app[0].tSend = 0s")
                w()
                w(f"**.ppp[*].queue.packetCapacity = {queueLength}")
                w()

                scenario_doc = f'xmldoc("../scenarios/experiment1/run{runNum}.xml")'
                w(f"*.scenarioManager.script = {scenario_doc}")
                if alg == "satcp":
                    w(f"**.tcp.scenario = {scenario_doc}")
                w()

    print("\nINI files generated!")


if __name__ == "__main__":
    main()