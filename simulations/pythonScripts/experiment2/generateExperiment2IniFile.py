#!/usr/bin/env python3

# Generates INI files for experiment 2 for each congestion control algorithm.
# Same style as the updated experiment 1/7 generators:
# - Adds satcp + leocc
# - Leocc: PingApp on clients + LeoccQueue everywhere
# - Satcp: **.tcp.scenario points at the same xmldoc as scenarioManager.script
# - Uses correct app indices (no app[*])

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
    queueLength = 340
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"]

    out_dir = Path("../../paperExperiments/experiment2")
    scenarios_dir = Path("../../paperExperiments/scenarios/experiment2")
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

    general_block = [
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
        "",
    ]

    for alg in algorithms:
        tcp_type, alg_class = ALG_FLAVOUR[alg]
        fileName = out_dir / f"experiment2_{alg}.ini"
        print(f"\nGenerating ini files for {alg}...")

        client_num_apps = 2 if alg == "leocc" else 1

        with fileName.open("w", encoding="utf-8") as f:
            def w(line: str = "") -> None:
                f.write(line + "\n")

            def block(lines) -> None:
                for line in lines:
                    w(line)

            # -------- [General] --------
            w("[General]")
            w()
            block(general_block)

            # -------- Algorithm block --------
            w(f'**.tcp.typename = "{tcp_type}"')
            w(f'**.tcp.tcpAlgorithmClass = "{alg_class}"')
            block(common_tcp)
            w()

            # Apps (correct indices)
            w(f"*.client[*].numApps = {client_num_apps}")
            block(common_app0)

            if alg == "leocc":
                w('*.client[*].app[1].typename = "LeoccPingApp"')
                w("*.client[*].app[1].startTime = 0s")
                w('*.client[*].app[1].destAddr = "server[0]"')
                w("*.client[*].app[1].sendInterval = 10ms")

            w()

            # Queue / knobs + initial ssthresh
            if alg in ("cubic", "satcp"):
                w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
                w()
                w(f"**.tcp.initialSsthresh = {400 * 1448}")
                w()

            elif alg in ("bbr", "bbr3"):
                w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
                w()
                # keep your experiment2 BBR value (you had 500*1448 for bbr, 4000*1448 for bbr3)
                if alg == "bbr":
                    w(f"**.tcp.initialSsthresh = {500 * 1448}")
                else:
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
                w(f"**.tcp.initialSsthresh = {400 * 1448}")
                w()

            # -------- Config sections --------
            for xmlFile in scenario_files:
                name = xmlFile.name
                if not (name.startswith("run") and name.endswith(".xml")):
                    continue

                runNum = int(name[3:-4])
                configName = f"{alg.title()}_LossRun{runNum}"

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

                scenario_doc = f'xmldoc("../scenarios/experiment2/run{runNum}.xml")'
                w(f"*.scenarioManager.script = {scenario_doc}")
                if alg == "satcp":
                    w(f"**.tcp.scenario = {scenario_doc}")
                w()

    print("\nINI files generated!")


if __name__ == "__main__":
    main()