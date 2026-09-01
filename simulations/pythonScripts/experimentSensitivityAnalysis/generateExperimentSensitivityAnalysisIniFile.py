#!/usr/bin/env python3

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from experimentSensitivityAnalysisSupport import (
    EXPERIMENT,
    FLOW_START_WINDOW_S,
    INI_FILE,
    LARGE_NON_BOTTLENECK_QUEUE_PACKETS,
    MSS_BYTES,
    PERSISTENT_SEND_BYTES,
    PINT_FEEDBACK_PROBABILITY,
    PINT_MAX_CONCURRENT_FLOWS,
    PINT_MAX_FLOW_COUNT,
    PINT_MAX_UTILIZATION,
    SELECTED_SKETCH_BITS,
    SIMULATION_TIME_S,
    TRANSIENT_HANDOVER_TIME_S,
    TRANSIENT_START_SPREAD_S,
    SimulationCase,
    cases,
    expected_simulation_count,
    trace_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import (  # noqa: E402
    common_load_libs,
    common_ned_path,
    ide_load_libs_enabled,
)


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = (
    SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT
).resolve()
SCENARIO_DIR = (
    SCRIPT_DIR / "../../paperExperiments/scenarios" / EXPERIMENT
).resolve()
NETWORK = (
    "orbtcpexperiments.simulations.paperExperiments."
    "experimentSensitivityAnalysis.dualdumbbell"
)


def w(output, line: str = "") -> None:
    output.write(line + "\n")


def load_trace(run: int) -> dict:
    path = SCENARIO_DIR / f"{trace_name(run)}.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing matched trace {path}; generate scenarios before the INI"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def write_general(output) -> None:
    w(output, "[General]")
    w(output, common_ned_path())
    if ide_load_libs_enabled():
        w(output, common_load_libs())
    w(output)
    w(output, f"network = {NETWORK}")
    w(output, f"sim-time-limit = {SIMULATION_TIME_S}s")
    w(output, "num-rngs = 2")
    w(output, "**.queue.rng-0 = 1")
    w(output, "record-eventlog = false")
    w(output, "cmdenv-express-mode = true")
    w(output, "cmdenv-redirect-output = false")
    w(output, "cmdenv-event-banners = false")
    w(output, "**.cmdenv-log-level = off")
    w(output, "**.scalar-recording = false")
    w(output, "**.vector-recording = false")
    w(output, "**.bin-recording = false")
    w(output)
    w(output, "*.configurator.optimizeRoutes = false")
    w(output, "**.tcp.typename = \"Orbtcp\"")
    w(output, "**.tcp.tcpAlgorithmClass = \"OrbtcpPintFlavour\"")
    w(output, "**.tcp.advertisedWindow = 200000000")
    w(output, "**.tcp.windowScalingSupport = true")
    w(output, "**.tcp.windowScalingFactor = -1")
    w(output, "**.tcp.increasedIWEnabled = true")
    w(output, "**.tcp.delayedAcksEnabled = false")
    w(output, "**.tcp.timestampSupport = true")
    w(output, "**.tcp.ecnWillingness = false")
    w(output, "**.tcp.nagleEnabled = true")
    w(output, "**.tcp.stopOperationTimeout = 4000s")
    w(output, f"**.tcp.mss = {MSS_BYTES}")
    w(output, "**.tcp.sackSupport = true")
    w(output, f"**.tcp.initialSsthresh = {4000 * MSS_BYTES}")
    w(output)
    w(output, "*.client[*].numApps = 1")
    w(output, "*.client[*].app[0].typename = \"TcpGoodputSessionApp\"")
    w(output, "*.client[*].app[0].tClose = -1s")
    w(output, f"*.client[*].app[0].sendBytes = {PERSISTENT_SEND_BYTES}")
    w(output, "*.client[*].app[0].dataTransferMode = \"bytecount\"")
    w(output, "*.client[*].app[0].statistic-recording = true")
    w(output, "*.server[*].numApps = 1")
    w(output, "*.server[*].app[0].typename = \"TcpSinkApp\"")
    w(
        output,
        "*.server[*].app[0].serverThreadModuleType = "
        "\"tcpgoodputapplications.applications.tcpapp."
        "TcpGoodputSinkAppThread\"",
    )
    w(output)
    w(output, "**.additiveIncreasePercent = 0.05")
    w(output, "**.eta = 0.95")
    w(output, "**.alpha = 0.01")
    w(output, "**.fixedAvgRTTVal = 0s")
    w(output)


def flow_start_times(case: SimulationCase, trace: dict) -> list[float]:
    workload = case.workload
    starts = []
    persistent_rng = random.Random(38_711 + case.run * 1_003)
    interval = FLOW_START_WINDOW_S / workload.persistent_flows
    for flow_index in range(workload.persistent_flows):
        centre = (flow_index + 0.5) * interval
        jitter = persistent_rng.uniform(-0.4 * interval, 0.4 * interval)
        starts.append(max(0.001, min(FLOW_START_WINDOW_S, centre + jitter)))

    if workload.transient_flows:
        state = next(
            state
            for state in trace["states"]
            if state["handover_time_s"] == TRANSIENT_HANDOVER_TIME_S
        )
        reconnect_time = float(state["reconnect_time_s"])
        transient_rng = random.Random(91_003 + case.run * 7_919)
        interval = TRANSIENT_START_SPREAD_S / workload.transient_flows
        for flow_index in range(workload.transient_flows):
            centre = (flow_index + 0.5) * interval
            jitter = transient_rng.uniform(-0.4 * interval, 0.4 * interval)
            starts.append(reconnect_time + 0.005 + max(0.0, centre + jitter))
    return starts


def recording_intervals(case: SimulationCase, trace: dict) -> str | None:
    if case.workload.experiment_key == "validation":
        return None
    if case.workload.experiment_key == "flow_isolation":
        state = next(
            state
            for state in trace["states"]
            if state["handover_time_s"] == TRANSIENT_HANDOVER_TIME_S
        )
        rtt_s = float(state["rtt_ms"]) / 1000
        start = max(0.0, float(state["reconnect_time_s"]) - rtt_s)
        end = min(
            SIMULATION_TIME_S,
            float(state["reconnect_time_s"]) + 10 * rtt_s,
        )
        return f"{start:.6f}..{end:.6f}"

    intervals = []
    for state in trace["states"][1:]:
        start = float(state["reconnect_time_s"])
        end = min(
            SIMULATION_TIME_S,
            start + 20 * float(state["rtt_ms"]) / 1000,
        )
        intervals.append(f"{start:.6f}..{end:.6f}")
    return ", ".join(intervals)


def enable_vector(output, metric: str, *, remove_repeats: bool = True) -> None:
    mode = "vector(removeRepeats)" if remove_repeats else "vector"
    w(output, f"**.{metric}:{mode}.vector-recording = true")
    w(output, f"**.{metric}.result-recording-modes = {mode}")


def write_recording_settings(output, case: SimulationCase, trace: dict) -> None:
    enable_vector(output, "goodput")
    enable_vector(output, "persistentQueueingDelay")
    if case.workload.experiment_key == "flow_isolation":
        # These epoch metrics may stay constant throughout a narrow recording
        # interval. Recording every emission preserves the control workload.
        enable_vector(output, "numberOfFlows", remove_repeats=False)
        enable_vector(
            output, "numOfFlowsInInitialPhase", remove_repeats=False
        )
    elif case.workload.experiment_key == "handover":
        enable_vector(output, "numberOfFlows")
        enable_vector(output, "numOfFlowsInInitialPhase")
        enable_vector(output, "pintLocalUtilization", remove_repeats=False)
        enable_vector(output, "pintDecodedUtilization", remove_repeats=False)
    else:
        enable_vector(output, "retransmissionRate")

    interval_spec = recording_intervals(case, trace)
    if interval_spec is not None:
        w(output, f"**.vector-recording-intervals = {interval_spec}")
    goodput_interval = (
        "20ms" if case.workload.experiment_key != "validation" else "1s"
    )
    w(output, f"**.goodputInterval = {goodput_interval}")
    w(output, f"**.throughputInterval = {goodput_interval}")


def write_queue_settings(output, case: SimulationCase, trace: dict) -> None:
    initial_capacity = int(trace["states"][0]["queue_packets"])
    # Fix the interface type so the runtime-mutable queue cannot fall back to
    # INET's non-mutable DropTailQueue through a wildcard type assignment.
    for transit in ("transitA", "transitB"):
        w(
            output,
            f"*.{transit}.ppp[1].typename = "
            '"orbtcp.linklayer.ppp.PintInterface"',
        )
    # Specific bottleneck capacities must precede the broad queue fallback.
    for transit in ("transitA", "transitB"):
        w(
            output,
            f"*.{transit}.ppp[1].queue.packetCapacity = {initial_capacity}",
        )
    w(
        output,
        f"**.ppp[*].queue.packetCapacity = "
        f"{LARGE_NON_BOTTLENECK_QUEUE_PACKETS}",
    )
    w(output, "**.**.queue.pintInitialRtt = 20ms")
    w(
        output,
        "**.**.queue.flowCountSketchEnabled = "
        f"{'true' if case.variant.flow_count_sketch else 'false'}",
    )
    w(output, f"**.**.queue.flowCardinalityBits = {SELECTED_SKETCH_BITS}")
    w(output, f"**.**.queue.flowSketchSeed = {1337 + case.run * 7919}")
    w(
        output,
        f"**.**.queue.pintFlowCountBits = {case.variant.flow_count_bits}",
    )
    w(output, f"**.**.queue.pintMaxFlowCount = {PINT_MAX_FLOW_COUNT}")
    w(output, f"**.**.queue.pintBits = {case.variant.utilization_bits}")
    w(output, "**.**.queue.pintAutoScaleEncoding = true")
    w(output, f"**.**.queue.pintMaxUtilization = {PINT_MAX_UTILIZATION:g}")
    w(
        output,
        f"**.**.queue.pintMaxConcurrentFlows = {PINT_MAX_CONCURRENT_FLOWS}",
    )


def write_transport_settings(output, case: SimulationCase) -> None:
    w(output, f"**.tcp.pintFlowCountBits = {case.variant.flow_count_bits}")
    w(output, f"**.tcp.pintMaxFlowCount = {PINT_MAX_FLOW_COUNT}")
    w(output, "**.tcp.pintUseInitialPhaseFlowCount = true")
    w(
        output,
        f"**.tcp.pintFeedbackProbability = {PINT_FEEDBACK_PROBABILITY:g}",
    )


def write_app_settings(output, case: SimulationCase, trace: dict) -> None:
    starts = flow_start_times(case, trace)
    if len(starts) != case.workload.total_flows:
        raise RuntimeError(f"Incorrect start-time count for {case.config_name}")
    for flow_index, start_time in enumerate(starts):
        w(
            output,
            f"*.client[{flow_index}].app[0].connectAddress = "
            f"\"server[{flow_index}]\"",
        )
        w(output, f"*.client[{flow_index}].app[0].tOpen = {start_time:.12g}s")
        w(output, f"*.client[{flow_index}].app[0].tSend = {start_time:.12g}s")
        if flow_index >= case.workload.persistent_flows:
            transient_bytes = case.workload.transient_packets * MSS_BYTES
            w(
                output,
                f"*.client[{flow_index}].app[0].sendBytes = {transient_bytes}B",
            )


def write_config(output, case: SimulationCase) -> None:
    trace = load_trace(case.run)
    w(output, f"[Config {case.config_name}]")
    w(output, "extends = General")
    w(output, f"seed-set = {case.run}")
    w(output, f"**.numberOfFlows = {case.workload.total_flows}")
    w(output)
    write_recording_settings(output, case, trace)
    w(output)
    write_queue_settings(output, case, trace)
    write_transport_settings(output, case)
    w(output)
    write_app_settings(output, case, trace)
    w(output)
    w(
        output,
        f"*.scenarioManager.script = "
        f"xmldoc(\"../scenarios/{EXPERIMENT}/{case.scenario_name}.xml\")",
    )
    w(output, f'output-vector-file = "results/{case.config_name}-#0.vec"')
    w(output, f'output-scalar-file = "results/{case.config_name}-#0.sca"')
    w(output)


def main() -> None:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPERIMENT_DIR / INI_FILE
    with path.open("w", encoding="utf-8") as output:
        write_general(output)
        for case in cases():
            write_config(output, case)
    print(
        f"Generated {expected_simulation_count()} configs in {path}: "
        "flow isolation, handover decomposition, and final validation."
    )


if __name__ == "__main__":
    main()
