#!/usr/bin/env python3

from __future__ import annotations

import random
import sys
from pathlib import Path

from experimentTuningSupport import (
    EXPERIMENT,
    FLOW_COUNTS,
    FLOW_JOIN_WINDOW_S,
    FULL_ORBCC,
    MSS_BYTES,
    PINT_VARIANTS,
    QUEUE_BDP_MULTIPLIER,
    RTT_MS,
    RUNS,
    SIMULATION_TIME_S,
    Variant,
    bottleneck_bandwidth_mbps,
    config_name,
    ini_name,
    queue_packets,
    scenario_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import common_ned_path


NETWORK = (
    "orbtcpexperiments.simulations.paperExperiments."
    "experimentTuning.singledumbbell"
)
LARGE_NON_BOTTLENECK_QUEUE_PACKETS = 100_000


def write_general(output, pint: bool) -> None:
    def w(line: str = "") -> None:
        output.write(line + "\n")

    w("[General]")
    w(common_ned_path())
    w()
    w(f"network = {NETWORK}")
    w(f"sim-time-limit = {SIMULATION_TIME_S}s")
    w("record-eventlog = false")
    w("cmdenv-express-mode = true")
    w("cmdenv-redirect-output = false")
    w("cmdenv-event-banners = false")
    w("**.cmdenv-log-level = off")
    w()

    tcp_vectors = (
        "cwnd",
        "rtt",
        "U",
        "tau",
        "queueingDelay",
        "sharingFlows",
    )
    queue_vectors = (
        "queueLength",
        "numberOfFlows",
        "effectiveNumberOfFlows",
        "pintLocalUtilization",
        "pintDecodedUtilization",
    )
    for metric in tcp_vectors:
        w(
            f"**.**.tcp.conn-*.{metric}:vector(removeRepeats)."
            "vector-recording = true"
        )
        w(
            f"**.**.tcp.conn-*.{metric}.result-recording-modes = "
            "vector(removeRepeats)"
        )
    for metric in queue_vectors:
        w(
            f"**.**.queue.{metric}:vector(removeRepeats)."
            "vector-recording = true"
        )
        w(
            f"**.**.queue.{metric}.result-recording-modes = "
            "vector(removeRepeats)"
        )
    w("**.**.goodput:vector(removeRepeats).vector-recording = true")
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
    w(f"**.tcp.initialSsthresh = {4000 * MSS_BYTES}")
    w()

    w("*.client[*].numApps = 1")
    w('*.client[*].app[0].typename = "TcpGoodputSessionApp"')
    w("*.client[*].app[0].tClose = -1s")
    w("*.client[*].app[0].sendBytes = 2GB")
    w('*.client[*].app[0].dataTransferMode = "bytecount"')
    w("*.client[*].app[0].statistic-recording = true")
    w("**.server[*].numApps = 1")
    w('**.server[*].app[0].typename = "TcpSinkApp"')
    w(
        '**.server[*].app[0].serverThreadModuleType = '
        '"tcpgoodputapplications.applications.tcpapp.'
        'TcpGoodputSinkAppThread"'
    )
    w()

    w("**.additiveIncreasePercent = 0.05")
    w("**.eta = 0.95")
    w("**.alpha = 0.01")
    w(f"**.fixedAvgRTTVal = {'0s' if pint else '0'}")

    if pint:
        w()
        w("# Common PINT range and sketch-memory settings.")
        w("**.**.queue.pintInitialRtt = 10ms")
        w("**.**.queue.flowCardinalityBits = 4096")
        w("**.**.queue.flowSketchSeed = 1337")
        w("**.pintMaxFlowCount = 65535")
        w("**.**.queue.pintAutoScaleEncoding = true")
        w("**.**.queue.pintMaxUtilization = 4")
        w("**.**.queue.pintMaxConcurrentFlows = 512")
    w()


def flow_start_times(flow_count: int, run: int) -> list[float]:
    rng = random.Random(1999 + (run - 1) + flow_count)
    interval = FLOW_JOIN_WINDOW_S / flow_count
    starts = []
    for flow_index in range(flow_count):
        centre = (flow_index + 1) * interval
        starts.append(max(0.01, rng.uniform(centre - 2.5, centre + 2.5)))
    return starts


def write_variant_settings(output, variant: Variant) -> None:
    if not variant.is_pint:
        return

    output.write(
        f"**.**.queue.flowCountSketchEnabled = "
        f"{'true' if variant.flow_count_sketch else 'false'}\n"
    )
    output.write(f"**.pintFlowCountBits = {variant.flow_count_bits}\n")
    output.write(f"**.**.queue.pintBits = {variant.utilization_bits}\n")
    output.write(
        f"**.tcp.pintFeedbackProbability = {variant.feedback_probability:.12g}\n"
    )


def write_config(output, variant: Variant, flow_count: int, run: int) -> None:
    name = config_name(variant, flow_count, run)
    queue_type = "PintQueue" if variant.is_pint else "IntQueue"

    output.write(f"[Config {name}]\n")
    output.write("extends = General\n")
    output.write(f"seed-set = {run}\n")
    output.write(f"**.numberOfFlows = {flow_count}\n")
    # OMNeT++ uses the first matching assignment, so this must precede the fallback.
    output.write(
        f'*.router1.ppp[{flow_count}].queue.typename = "{queue_type}"\n'
    )
    output.write('**.ppp[*].queue.typename = "DropTailQueue"\n')
    output.write(
        f"# {QUEUE_BDP_MULTIPLIER} BDP at "
        f"{bottleneck_bandwidth_mbps(flow_count)} Mbps and {RTT_MS} ms.\n"
    )
    output.write(
        f"*.router1.ppp[{flow_count}].queue.packetCapacity = "
        f"{queue_packets(flow_count)}\n"
    )
    output.write(
        f"**.ppp[*].queue.packetCapacity = "
        f"{LARGE_NON_BOTTLENECK_QUEUE_PACKETS}\n"
    )
    write_variant_settings(output, variant)
    output.write("\n")

    for flow_index, start_time in enumerate(flow_start_times(flow_count, run)):
        output.write(
            f'*.client[{flow_index}].app[0].connectAddress = '
            f'"server[{flow_index}]"\n'
        )
        output.write(
            f"*.client[{flow_index}].app[0].tOpen = {start_time:.12g}s\n"
        )
        output.write(
            f"*.client[{flow_index}].app[0].tSend = {start_time:.12g}s\n"
        )

    scenario = (
        f'xmldoc("../scenarios/{EXPERIMENT}/'
        f'{scenario_name(flow_count, run)}.xml")'
    )
    output.write(f"*.scenarioManager.script = {scenario}\n")
    output.write(f'output-vector-file = "results/{name}-#0.vec"\n')
    output.write(f'output-scalar-file = "results/{name}-#0.sca"\n\n')


def write_ini(path: Path, variants: tuple[Variant, ...], pint: bool) -> None:
    with path.open("w", encoding="utf-8") as output:
        write_general(output, pint)
        for variant in variants:
            for flow_count in FLOW_COUNTS:
                for run in RUNS:
                    write_config(output, variant, flow_count, run)


def main() -> None:
    out_dir = Path("../../paperExperiments") / EXPERIMENT
    out_dir.mkdir(parents=True, exist_ok=True)
    write_ini(out_dir / ini_name(False), (FULL_ORBCC,), pint=False)
    write_ini(out_dir / ini_name(True), PINT_VARIANTS, pint=True)
    config_count = len(FLOW_COUNTS) * len(RUNS) * (1 + len(PINT_VARIANTS))
    print(
        f"Generated {config_count} {EXPERIMENT} configs: one OrbCC baseline, "
        f"{len(PINT_VARIANTS)} unique PINT variants, {len(FLOW_COUNTS)} flow loads, "
        f"and {len(RUNS)} runs. Exact PINT is shared across all feature sweeps."
    )


if __name__ == "__main__":
    main()
