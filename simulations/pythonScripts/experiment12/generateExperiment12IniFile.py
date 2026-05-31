#!/usr/bin/env python3

from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import clone_raynet_ini_variants, common_ned_path


BANDWIDTH_MBPS = 100
BASE_RTT_S = 0.020
MSS_BYTES = 1448
QUEUE_BDP_MULTIPLIER = 5
LARGE_NON_BOTTLENECK_QUEUE_PACKETS = 100000
RUNS = 5


def bottleneck_queue_packets() -> int:
    bandwidth_bytes_per_second = BANDWIDTH_MBPS * 125000
    return int((bandwidth_bytes_per_second * BASE_RTT_S * QUEUE_BDP_MULTIPLIER) / MSS_BYTES)


def write_ini(out_file: Path, protocol: str) -> None:
    if protocol == "cubic":
        tcp_type = "TcpPaced"
        algorithm_class = "TcpCubic"
        initial_ssthresh = 400 * MSS_BYTES
    elif protocol == "bbr":
        tcp_type = "Bbr"
        algorithm_class = "BbrFlavour"
        initial_ssthresh = 4000 * MSS_BYTES
    else:
        raise ValueError(f"Unsupported source protocol: {protocol}")

    queue_packets = bottleneck_queue_packets()
    with out_file.open("w", encoding="utf-8") as f:
        def w(line: str = "") -> None:
            f.write(line + "\n")

        w("[General]")
        w(common_ned_path())
        w()
        w("network = orbtcpexperiments.simulations.paperExperiments.experiment12.singledumbbell")
        w("sim-time-limit = 100s")
        w("record-eventlog=false")
        w("cmdenv-express-mode = true")
        w("cmdenv-redirect-output = false")
        w("cmdenv-output-file = experiment12Log.txt")
        w("cmdenv-log-prefix = %t | %m |")
        w("cmdenv-event-banners = false")
        w("**.cmdenv-log-level = off")
        w()
        w("**.**.tcp.conn-*.rtt:vector(removeRepeats).vector-recording = true")
        w("**.**.tcp.conn-*.rtt.result-recording-modes = vector(removeRepeats)")
        w("**.**.goodput:vector(removeRepeats).vector-recording = true")
        w("**.**.goodput.result-recording-modes = vector(removeRepeats)")
        w("**.scalar-recording=false")
        w("**.vector-recording=false")
        w("**.bin-recording=false")
        w()
        w("**.goodputInterval = 1s")
        w("**.throughputInterval = 1s")
        w("*.configurator.optimizeRoutes = false")
        w()
        w(f'**.tcp.typename = "{tcp_type}"')
        w(f'**.tcp.tcpAlgorithmClass = "{algorithm_class}"')
        w("**.tcp.advertisedWindow = 200000000")
        w("**.tcp.windowScalingSupport = true")
        w("**.tcp.windowScalingFactor = -1")
        w("**.tcp.increasedIWEnabled = true")
        w("**.tcp.delayedAcksEnabled = false")
        w("**.tcp.timestampSupport = true")
        w("**.tcp.ecnWillingness = false")
        w("**.tcp.nagleEnabled = true")
        w("**.tcp.stopOperationTimeout = 4000s")
        w(f"**.tcp.mss = {MSS_BYTES}")
        w("**.tcp.sackSupport = true")
        w()
        w("*.client[*].numApps = 1")
        w('*.client[*].app[0].typename = "TcpGoodputSessionApp"')
        w("*.client[*].app[0].tClose = -1s")
        w("*.client[*].app[0].sendBytes = 2GB")
        w('*.client[*].app[0].dataTransferMode = "bytecount"')
        w("*.client[*].app[0].statistic-recording = true")
        w()
        w("**.server[*].numApps = 1")
        w('**.server[*].app[0].typename = "TcpSinkApp"')
        w('**.server[*].app[0].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"')
        w()
        w('**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"')
        # OMNeT++ uses the first matching ini assignment. Keep the bottleneck
        # capacities before the large wildcard for the access-link queues.
        w(f"**.router1.ppp[1].queue.packetCapacity = {queue_packets}")
        w(f"**.router2.ppp[1].queue.packetCapacity = {queue_packets}")
        w(f"**.ppp[*].queue.packetCapacity = {LARGE_NON_BOTTLENECK_QUEUE_PACKETS}")
        w(f"**.tcp.initialSsthresh = {initial_ssthresh}")
        w()

        for run in range(1, RUNS + 1):
            rng = random.Random(1999 + run)
            start_time = rng.uniform(0, 0.1)
            config_name = f"{protocol.title()}_Run{run}"
            w(f"[Config {config_name}]")
            w("extends = General")
            w("**.numberOfFlows = 1")
            w('*.client[0].app[0].connectAddress = "server[0]"')
            w(f"*.client[0].app[0].tOpen = {start_time}s")
            w(f"*.client[0].app[0].tSend = {start_time}s")
            w(f'output-vector-file = "results/{config_name}-#0.vec"')
            w(f'output-scalar-file = "results/{config_name}-#0.sca"')
            w('*.scenarioManager.script = xmldoc("../scenarios/experiment12/reconfigurations.xml")')
            w()


def main() -> None:
    out_dir = Path("../../paperExperiments/experiment12")
    out_dir.mkdir(parents=True, exist_ok=True)

    write_ini(out_dir / "experiment12_cubic.ini", "cubic")
    bbr_source = out_dir / "experiment12_bbr.ini"
    write_ini(bbr_source, "bbr")
    clone_raynet_ini_variants(bbr_source)
    bbr_source.unlink()

    print(
        "Generated experiment 12 Cubic and Orca ini files with "
        f"{bottleneck_queue_packets()} packets at the 5 BDP bottleneck."
    )


if __name__ == "__main__":
    main()
