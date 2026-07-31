#!/usr/bin/env python3

from __future__ import annotations

import random
import sys
from pathlib import Path

from experiment13Support import (
    FULL_ORBCC,
    MSS_BYTES,
    PINT_VARIANTS,
    QUEUE_PACKETS,
    RUNS,
    SIMULATION_TIME_S,
    VARIANTS,
    WORKLOADS,
    config_name,
    ini_name,
    scenario_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import common_ned_path


LARGE_NON_BOTTLENECK_QUEUE_PACKETS = 100000
PINT_SETTINGS = (
    "**.**.queue.pintInitialRtt = 10ms",
    "**.**.queue.flowCardinalityBits = 4096",
    "**.**.queue.flowSketchSeed = 1337",
    "**.**.queue.pintBits = 8",
    "**.**.queue.pintLogBase = 1.05",
    "**.**.queue.pintMaxConcurrentFlows = 512",
)


def write_general(f, pint: bool) -> None:
    def w(line: str = "") -> None:
        f.write(line + "\n")

    w("[General]")
    w(common_ned_path())
    w()
    w("network = orbtcpexperiments.simulations.paperExperiments.experiment13.singledumbbell")
    w(f"sim-time-limit = {SIMULATION_TIME_S}s")
    w("record-eventlog = false")
    w("cmdenv-express-mode = true")
    w("cmdenv-redirect-output = false")
    w("cmdenv-event-banners = false")
    w("**.cmdenv-log-level = off")
    w()
    for metric in ("cwnd", "rtt", "U", "tau", "queueingDelay"):
        w(f"**.**.tcp.conn-*.{metric}:vector(removeRepeats).vector-recording = true")
    w("**.**.goodput:vector(removeRepeats).vector-recording = true")
    w("**.**.tcp.conn-*.**.result-recording-modes = vector(removeRepeats)")
    w("**.**.goodput.result-recording-modes = vector(removeRepeats)")
    w("**.scalar-recording = false")
    w("**.vector-recording = false")
    w("**.bin-recording = false")
    w()
    w("**.goodputInterval = 1s")
    w("**.throughputInterval = 1s")
    w("*.configurator.optimizeRoutes = false")
    w()
    algorithm_class = "OrbtcpPintFlavour" if pint else "OrbtcpFlavour"
    bottleneck_queue = "PintQueue" if pint else "IntQueue"
    w('**.tcp.typename = "Orbtcp"')
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
    w("**.tcp.initialSsthresh = 5792000")
    w()
    w("*.client.numApps = 1")
    w('*.client.app[0].typename = "TcpGoodputSessionApp"')
    w("*.client.app[0].tClose = -1s")
    w("*.client.app[0].sendBytes = 2GB")
    w('*.client.app[0].dataTransferMode = "bytecount"')
    w("*.client.app[0].statistic-recording = true")
    w("*.server.numApps = 1")
    w('*.server.app[0].typename = "TcpSinkApp"')
    w('*.server.app[0].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"')
    w()
    w(f'*.router1.ppp[1].queue.typename = "{bottleneck_queue}"')
    w(f"*.router1.ppp[1].queue.packetCapacity = {QUEUE_PACKETS}")
    w(f"*.router2.ppp[1].queue.packetCapacity = {QUEUE_PACKETS}")
    w('**.ppp[*].queue.typename = "DropTailQueue"')
    w(f"**.ppp[*].queue.packetCapacity = {LARGE_NON_BOTTLENECK_QUEUE_PACKETS}")
    w("**.additiveIncreasePercent = 0.05")
    w("**.eta = 0.95")
    w("**.alpha = 0.01")
    w("**.fixedAvgRTTVal = 0s")
    if pint:
        w()
        w("# OrbCC-PINT encoding and sampling settings.")
        for setting in PINT_SETTINGS:
            w(setting)
    w()


def write_config(f, variant, workload: str, run: int) -> None:
    name = config_name(variant, workload, run)
    start_time_s = random.Random(13000 + run).uniform(0.0, 0.1)
    f.write(f"[Config {name}]\n")
    f.write("extends = General\n")
    # Sampling variants share RNG decisions within a run; lower probabilities are
    # deterministic subsets of the higher-probability feedback opportunities.
    f.write(f"seed-set = {run}\n")
    f.write("**.numberOfFlows = 1\n")
    if variant.probability is not None:
        f.write(f"**.tcp.pintFeedbackProbability = {variant.probability}\n")
    f.write('*.client.app[0].connectAddress = "server"\n')
    f.write(f"*.client.app[0].tOpen = {start_time_s}s\n")
    f.write(f"*.client.app[0].tSend = {start_time_s}s\n")
    f.write(f'output-vector-file = "results/{name}-#0.vec"\n')
    f.write(f'output-scalar-file = "results/{name}-#0.sca"\n')
    f.write(f'*.scenarioManager.script = xmldoc("../scenarios/experiment13/{scenario_name(workload, run)}.xml")\n\n')


def write_ini(path: Path, variants) -> None:
    pint = variants[0].is_pint
    with path.open("w", encoding="utf-8") as f:
        write_general(f, pint)
        for workload in WORKLOADS:
            for variant in variants:
                for run in RUNS:
                    write_config(f, variant, workload, run)


def main() -> None:
    out_dir = Path("../../paperExperiments/experiment13")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_ini(out_dir / ini_name(FULL_ORBCC), (FULL_ORBCC,))
    write_ini(out_dir / ini_name(PINT_VARIANTS[0]), PINT_VARIANTS)
    print(
        f"Generated Experiment 13 with {len(VARIANTS)} variants, {len(WORKLOADS)} workloads, "
        f"and {len(RUNS)} matched runs per variant."
    )


if __name__ == "__main__":
    main()
