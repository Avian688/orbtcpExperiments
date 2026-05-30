#!/usr/bin/env python3

import json
import math
import random
from pathlib import Path


BASE_BW_MBPS = 100
BASE_RTT_S = 0.05
MSS_BYTES = 1448
RUNS = 5
SIM_TIME_LIMIT_S = 120
EXPERIMENT0_NED_PATHS = (
    "../..",
    "../../../src",
    "../../../../bbr/simulations",
    "../../../../bbr/src",
    "../../../../inet4.5/examples",
    "../../../../inet4.5/showcases",
    "../../../../inet4.5/src",
    "../../../../inet4.5/tests/validation",
    "../../../../inet4.5/tests/networks",
    "../../../../inet4.5/tutorials",
    "../../../../tcpPaced/src",
    "../../../../tcpPaced/simulations",
    "../../../../tcpGoodputApplications/simulations",
    "../../../../tcpGoodputApplications/src",
)

VARIANTS = [
    {
        "key": "no_updated_sack_no_pacing_no_rack",
        "config": "Bbr3_NoUpdatedSackNoPacingNoRack",
        "label": "No updated SACK, no pacing, no RACK",
        "updated_sack": False,
        "pacing": False,
        "rack": False,
    },
    {
        "key": "updated_sack_no_pacing_no_rack",
        "config": "Bbr3_UpdatedSackNoPacingNoRack",
        "label": "Updated SACK, no pacing, no RACK",
        "updated_sack": True,
        "pacing": False,
        "rack": False,
    },
    {
        "key": "updated_sack_pacing_no_rack",
        "config": "Bbr3_UpdatedSackPacingNoRack",
        "label": "Updated SACK, pacing, no RACK",
        "updated_sack": True,
        "pacing": True,
        "rack": False,
    },
    {
        "key": "all_enabled",
        "config": "Bbr3_AllEnabled",
        "label": "Updated SACK, pacing, RACK",
        "updated_sack": True,
        "pacing": True,
        "rack": True,
    },
]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def bdp_packets() -> int:
    bytes_in_bdp = (BASE_BW_MBPS * 1_000_000 / 8) * BASE_RTT_S
    return math.ceil(bytes_in_bdp / MSS_BYTES)


def load_start_times() -> dict[str, float]:
    path = Path("../../paperExperiments/startTimes/experiment0/start_times.json")
    if path.is_file():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {str(key): float(value) for key, value in raw.items()}

    rng = random.Random(0)
    return {f"run{run}": round(rng.uniform(0.0, 0.1), 6) for run in range(1, RUNS + 1)}


def experiment0_ned_path() -> str:
    return "ned-path = " + ":".join(EXPERIMENT0_NED_PATHS)


def main() -> None:
    out_dir = Path("../../paperExperiments/experiment0")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "experiment0_bbr3.ini"
    start_times = load_start_times()
    queue_packets = bdp_packets()

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

    with out_file.open("w", encoding="utf-8") as f:
        def w(line: str = "") -> None:
            f.write(line + "\n")

        def block(lines) -> None:
            for line in lines:
                w(line)

        w("[General]")
        w(experiment0_ned_path())
        w()
        block(
            [
                "network = orbtcpexperiments.simulations.paperExperiments.experiment0.singledumbbell",
                f"sim-time-limit = {SIM_TIME_LIMIT_S}s",
                "record-eventlog=false",
                "cmdenv-express-mode = true",
                "cmdenv-redirect-output = false",
                "cmdenv-output-file = experiment0Log.txt",
                "cmdenv-log-prefix = %t | %m |",
                "cmdenv-event-banners = false",
                "**.cmdenv-log-level = off",
                "",
                "**.**.tcp.conn-*.cwnd:vector(removeRepeats).vector-recording = true",
                "**.**.tcp.conn-*.cwnd.result-recording-modes = vector(removeRepeats)",
                "**.**.goodput:vector(removeRepeats).vector-recording = true",
                "**.**.goodput.result-recording-modes = vector(removeRepeats)",
                "",
                "**.scalar-recording=false",
                "**.vector-recording=false",
                "**.bin-recording=false",
                "",
                "**.goodputInterval = 1s",
                "**.throughputInterval = 1s",
                "",
                '**.tcp.typename = "Bbr"',
                '**.tcp.tcpAlgorithmClass = "Bbr3Flavour"',
            ]
        )
        block(common_tcp)
        w()
        block(
            [
                "*.client[*].numApps = 1",
                '*.client[*].app[0].typename  = "TcpGoodputSessionApp"',
                "*.client[*].app[0].tClose = -1s",
                "*.client[*].app[0].sendBytes = 2GB",
                '*.client[*].app[0].dataTransferMode = "bytecount"',
                "*.client[*].app[0].statistic-recording = true",
                "",
                "**.server[*].numApps = 1",
                '**.server[*].app[0].typename  = "TcpSinkApp"',
                '**.server[*].app[0].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"',
                "",
                '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"',
                "**.ppp[*].queue.packetCapacity = 100000",
                f"**.router1.ppp[1].queue.packetCapacity = {queue_packets}",
                f"**.router2.ppp[1].queue.packetCapacity = {queue_packets}",
                f"**.tcp.initialSsthresh = {4000 * MSS_BYTES}",
            ]
        )
        w()

        for variant in VARIANTS:
            for run in range(1, RUNS + 1):
                config_name = f"{variant['config']}_Run{run}"
                start_time = start_times[f"run{run}"]
                w(f"[Config {config_name}]")
                w("extends = General")
                w()
                w(f"# {variant['label']}")
                w(f"**.updatedSackEnabled = {bool_text(variant['updated_sack'])}")
                w(f"**.pacingEnabled = {bool_text(variant['pacing'])}")
                w(f"**.rackEnabled = {bool_text(variant['rack'])}")
                w()
                w("**.numberOfFlows = 1")
                w('*.client[0].app[0].connectAddress = "server[0]"')
                w(f"*.client[0].app[0].tOpen = {start_time}s")
                w(f"*.client[0].app[0].tSend = {start_time}s")
                w()
                w(f'output-vector-file = "results/{config_name}-#0.vec"')
                w(f'output-scalar-file = "results/{config_name}-#0.sca"')
                w(f'*.scenarioManager.script = xmldoc("../scenarios/experiment0/run{run}.xml")')
                w()

    print(f"Generated {out_file} with {queue_packets} packets for 1 BDP.")


if __name__ == "__main__":
    main()
