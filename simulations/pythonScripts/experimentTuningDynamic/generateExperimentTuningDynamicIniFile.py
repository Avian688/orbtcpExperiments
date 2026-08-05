#!/usr/bin/env python3

from __future__ import annotations

import random
import sys
from pathlib import Path

from experimentTuningDynamicSupport import (
    CONDITIONS,
    EXPERIMENT,
    FLOW_COUNTS,
    FLOW_START_WINDOW_S,
    FULL_ORBCC,
    MSS_BYTES,
    PINT_VARIANTS,
    QUEUE_PACKETS,
    RUNS,
    SIMULATION_TIME_S,
    Variant,
    config_name,
    expected_simulation_count,
    ini_name,
    scenario_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import common_load_libs, common_ned_path  # noqa: E402


NETWORK = (
    "orbtcpexperiments.simulations.paperExperiments."
    "experimentTuningDynamic.singledumbbell"
)
LARGE_NON_BOTTLENECK_QUEUE_PACKETS = 100_000


def write_recording_settings(output) -> None:
    def w(line: str = "") -> None:
        output.write(line + "\n")

    for metric in ("retransmissionRate",):
        w(
            f"**.**.tcp.conn-*.{metric}:vector(removeRepeats)."
            "vector-recording = true"
        )
        w(
            f"**.**.tcp.conn-*.{metric}.result-recording-modes = "
            "vector(removeRepeats)"
        )
    w("**.**.queue.queueLength:vector(removeRepeats).vector-recording = true")
    w(
        "**.**.queue.queueLength.result-recording-modes = "
        "vector(removeRepeats)"
    )
    w("**.**.goodput:vector(removeRepeats).vector-recording = true")
    w("**.**.goodput.result-recording-modes = vector(removeRepeats)")
    w("**.scalar-recording = false")
    w("**.vector-recording = false")
    w("**.bin-recording = false")


def write_general(output, pint: bool) -> None:
    def w(line: str = "") -> None:
        output.write(line + "\n")

    w("[General]")
    w(common_ned_path())
    w(common_load_libs())
    w()
    w(f"network = {NETWORK}")
    w(f"sim-time-limit = {SIMULATION_TIME_S}s")
    w("record-eventlog = false")
    w("cmdenv-express-mode = true")
    w("cmdenv-redirect-output = false")
    w("cmdenv-event-banners = false")
    w("**.cmdenv-log-level = off")
    w()
    write_recording_settings(output)
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
        w("# Common exact-range and sketch-memory settings.")
        w("**.**.queue.pintInitialRtt = 10ms")
        w("**.**.queue.flowCardinalityBits = 4096")
        w("**.**.queue.flowSketchSeed = 1337")
        w("**.pintMaxFlowCount = 65535")
        w("**.**.queue.pintAutoScaleEncoding = true")
        w("**.**.queue.pintMaxUtilization = 4")
        w("**.**.queue.pintMaxConcurrentFlows = 512")
    w()


def flow_start_times(flow_count: int, run: int) -> list[float]:
    rng = random.Random(38_711 + run * 1_003 + flow_count)
    interval = FLOW_START_WINDOW_S / flow_count
    starts = []
    for flow_index in range(flow_count):
        centre = (flow_index + 0.5) * interval
        jitter = rng.uniform(-0.4 * interval, 0.4 * interval)
        starts.append(max(0.001, min(FLOW_START_WINDOW_S, centre + jitter)))
    return starts


def write_variant_settings(output, variant: Variant) -> None:
    if not variant.is_pint:
        return
    output.write(
        "**.**.queue.flowCountSketchEnabled = "
        f"{'true' if variant.flow_count_sketch else 'false'}\n"
    )
    output.write(f"**.pintFlowCountBits = {variant.flow_count_bits}\n")
    output.write(f"**.**.queue.pintBits = {variant.utilization_bits}\n")
    output.write(
        f"**.tcp.pintFeedbackProbability = "
        f"{variant.feedback_probability:.12g}\n"
    )


def write_config(
    output,
    variant: Variant,
    flow_count: int,
    condition,
    run: int,
) -> None:
    name = config_name(variant, flow_count, condition, run)
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
        f"*.router1.ppp[{flow_count}].queue.packetCapacity = {QUEUE_PACKETS}\n"
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
        f'{scenario_name(flow_count, condition, run)}.xml")'
    )
    output.write(f"*.scenarioManager.script = {scenario}\n")
    output.write(f'output-vector-file = "results/{name}-#0.vec"\n')
    output.write(f'output-scalar-file = "results/{name}-#0.sca"\n\n')


def write_ini(path: Path, variants: tuple[Variant, ...], pint: bool) -> None:
    with path.open("w", encoding="utf-8") as output:
        write_general(output, pint)
        for variant in variants:
            for flow_count in FLOW_COUNTS:
                for condition in CONDITIONS:
                    for run in RUNS:
                        write_config(output, variant, flow_count, condition, run)


def main() -> None:
    out_dir = Path("../../paperExperiments") / EXPERIMENT
    out_dir.mkdir(parents=True, exist_ok=True)
    write_ini(out_dir / ini_name(False), (FULL_ORBCC,), pint=False)
    write_ini(out_dir / ini_name(True), PINT_VARIANTS, pint=True)
    print(
        f"Generated {expected_simulation_count()} {EXPERIMENT} configs: "
        f"{1 + len(PINT_VARIANTS)} implementations, {len(FLOW_COUNTS)} "
        f"flow loads, {len(CONDITIONS)} conditions, and {len(RUNS)} runs."
    )


if __name__ == "__main__":
    main()
