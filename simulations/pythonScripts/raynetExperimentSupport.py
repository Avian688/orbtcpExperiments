#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

RAYNET_PROTOCOLS = []

RAYNET_ALG_FLAVOUR = {
    "orca": ("OrcaTcp", "Orca"),
    "cleanslate": ("CleanSlateTcp", "CleanSlate"),
    "astrea": ("AstreaTcp", "Astrea"),
}

_RAYNET_CONFIG_ALIAS = {
    "cleanslate": "CleanSlate",
    "astrea": "Astrea",
}

_PROTOCOL_CONFIG_PREFIX = {
    "orbtcp_pint": "OrbtcpPint",
}


def _looks_like_raynet_home(path: Path) -> bool:
    return (
        (path / "raynet_paths.py").is_file()
        and (path / "simlibs" / "RLComponents" / "src").is_dir()
        and (path / "_scripts" / "run" / "raynet_runner.py").is_file()
    )


def _candidate_raynet_homes() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("RAYNET_HOME")
    if configured:
        candidates.append(Path(configured).expanduser())

    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        candidates.append(parent / "raynet")
        if parent.name.startswith("omnetpp"):
            candidates.append(parent.parent / "raynet")

    candidates.extend(
        [
            Path.home() / "harddrive" / "raynet",
            Path.home() / "raynet",
        ]
    )
    return candidates


def _resolve_raynet_home() -> Path:
    candidates = _candidate_raynet_homes()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if _looks_like_raynet_home(resolved):
            return resolved
    return candidates[0].resolve(strict=False)


RAYNET_HOME = _resolve_raynet_home()
os.environ.setdefault("RAYNET_HOME", str(RAYNET_HOME))
RAYNET_SIMULATION_ROOT = os.environ.get("RAYNET_SIMULATION_ROOT", "../../../../../../raynet")


def _raynet_simulation_path(*parts: str) -> str:
    return str(Path(RAYNET_SIMULATION_ROOT, *parts))

BASE_NED_PATHS = (
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
    "../../../../cubic/simulations",
    "../../../../cubic/src",
    "../../../../orbtcp/simulations",
    "../../../../orbtcp/src",
    "../../../../satcp/simulations",
    "../../../../satcp/src",
    "../../../../leocc/simulations",
    "../../../../leocc/src",
    "../../../../tcpGoodputApplications/simulations",
    "../../../../tcpGoodputApplications/src",
)

LEO_NED_PATHS = (
    "../../../../leosatellites/simulations",
    "../../../../leosatellites/src",
    "../../../../os3/simulations",
    "../../../../os3/src",
)

RAYNET_NED_PATHS = (
    _raynet_simulation_path("simlibs", "RLComponents", "src"),
    _raynet_simulation_path("simlibs", "Orca", "src"),
    _raynet_simulation_path("simlibs", "CleanSlate", "src"),
    _raynet_simulation_path("simlibs", "Astrea", "src"),
)

RAYNET_IDE_LIBS = (
    _raynet_simulation_path("simlibs", "RLComponents", "src", "RLComponents"),
    _raynet_simulation_path("simlibs", "Orca", "src", "Orca"),
    _raynet_simulation_path("simlibs", "CleanSlate", "src", "CleanSlate"),
    _raynet_simulation_path("simlibs", "Astrea", "src", "Astrea"),
)

BASE_LIBS = (
    "../../../src/orbtcpExperiments",
    "../../../../bbr/src/bbr",
    "../../../../inet4.5/src/INET",
    "../../../../tcpPaced/src/tcpPaced",
    "../../../../cubic/src/cubic",
    "../../../../orbtcp/src/orbtcp",
    "../../../../satcp/src/satcp",
    "../../../../leocc/src/leocc",
    "../../../../tcpGoodputApplications/src/tcpGoodputApplications",
)

LEO_LIBS = (
    "../../../../leosatellites/src/leosatellites",
    "../../../../os3/src/os3",
)


def is_raynet_protocol(protocol: str) -> bool:
    return protocol.lower() in RAYNET_PROTOCOLS


def raynet_debug_output_enabled() -> bool:
    value = os.environ.get("RAYNET_DEBUG_OUTPUT", os.environ.get("RAYNET_VERBOSE", ""))
    return value.lower() in {"1", "true", "yes", "on", "debug", "verbose"}


def simulation_output_kwargs(protocol: str):
    if is_raynet_protocol(protocol) and raynet_debug_output_enabled():
        return {}
    return {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}


def with_raynet_protocols(protocols):
    result = list(protocols)
    for protocol in RAYNET_PROTOCOLS:
        if protocol not in result:
            result.append(protocol)
    return result


def with_experiment_protocols(protocols):
    result = []
    for protocol in protocols:
        if protocol not in result:
            result.append(protocol)
        if protocol.lower() == "orbtcp" and "orbtcp_pint" not in result:
            result.append("orbtcp_pint")
    return with_raynet_protocols(result)


def protocol_config_prefix(protocol: str) -> str:
    return _PROTOCOL_CONFIG_PREFIX.get(protocol.lower(), protocol.title())


def common_ned_path(include_leo: bool = False) -> str:
    paths = list(BASE_NED_PATHS)
    if include_leo:
        paths.extend(LEO_NED_PATHS)
    paths.extend(str(path) for path in RAYNET_NED_PATHS)
    return "ned-path = " + ":".join(paths)


def common_load_libs() -> str:
    return "load-libs = " + " ".join(RAYNET_IDE_LIBS)


def ide_load_libs_enabled() -> bool:
    return os.environ.get("RAYNET_ENABLE_IDE_LOAD_LIBS", "").lower() in {"1", "true", "yes", "on"}


def ensure_local_ini_preamble(text: str, include_leo: bool = False) -> str:
    first_config = text.find("\n[Config ")
    general_text = text if first_config == -1 else text[:first_config]
    config_text = "" if first_config == -1 else text[first_config:]

    general_text = re.sub(
        r"(?m)^(?:ned-path|load-libs)\s*=.*(?:\n|$)",
        "",
        general_text,
    )
    marker = "[General]\n"
    if marker not in general_text:
        raise ValueError("Cannot add local INI paths: missing [General] section")

    preamble_lines = [common_ned_path(include_leo)]
    if ide_load_libs_enabled():
        preamble_lines.append(common_load_libs())
    preamble = "\n".join(preamble_lines) + "\n"
    general_text = general_text.replace(marker, marker + preamble, 1)
    return general_text + config_text


def build_opp_run_command(config_name: str, ini_file: str, include_leo: bool = False):
    ned_paths = list(BASE_NED_PATHS)
    if include_leo:
        ned_paths.extend(LEO_NED_PATHS)
    ned_paths.append(_raynet_simulation_path("simlibs", "RLComponents", "src"))

    image_path = "../../../../inet4.5/images"
    if include_leo:
        image_path += ":../../../../os3/images"

    libs = list(BASE_LIBS)
    if include_leo:
        libs.extend(LEO_LIBS)
    libs.append(_raynet_simulation_path("simlibs", "RLComponents", "src", "RLComponents"))

    command = [
        "opp_run",
        "-r",
        "0",
        "-m",
        "-u",
        "Cmdenv",
        "-c",
        config_name,
        "-n",
        ":".join(ned_paths),
        f"--image-path={image_path}",
        "--*.visualizer.typename=\"\"",
    ]
    for lib in libs:
        command.extend(["-l", lib])
    command.append(ini_file)
    return command


def build_simulation_command(protocol: str, ini_file: str, config_name: str, include_leo: bool = False):
    if is_raynet_protocol(protocol):
        return [
            sys.executable,
            str(Path(__file__).resolve().parent / "runRaynetProtocol.py"),
            protocol.lower(),
            ini_file,
            config_name,
        ]
    return build_opp_run_command(config_name, ini_file, include_leo=include_leo)


@dataclass(frozen=True)
class SimulationConfig:
    protocol: str
    ini_file: str
    config_name: str
    include_leo: bool = False


@dataclass
class _RunningSimulation:
    config: SimulationConfig
    process: subprocess.Popen
    started: float
    log_file: object | None
    log_path: Path | None


_ACTIVE_SIMULATION_PROCESSES: dict[int, subprocess.Popen] = {}
_PROCESS_GROUP_TERMINATION_GRACE_SECONDS = 2


def collect_simulation_configs(
    protocol: str,
    ini_file: str,
    run_list,
    cwd,
    include_leo: bool = False,
) -> list[SimulationConfig]:
    ini_path = Path(cwd) / ini_file
    run_numbers = set(run_list)
    run_re = re.compile(r"Run(\d{1,5})\]")
    configs = []

    for line in ini_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("[Config "):
            continue
        match = run_re.search(line)
        if match and int(match.group(1)) in run_numbers:
            configs.append(SimulationConfig(protocol, ini_file, line[8:-1], include_leo))

    return configs


def _result_paths(config: SimulationConfig, cwd: Path) -> tuple[Path, Path]:
    prefix = cwd / "results" / config.config_name
    return prefix.with_name(prefix.name + "-#0.vec"), prefix.with_name(prefix.name + "-#0.sca")


def _completion_marker_path(config: SimulationConfig, cwd: Path) -> Path:
    return cwd / "results" / f"{config.config_name}-#0.complete.json"


def _result_signature(config: SimulationConfig, cwd: Path):
    signature = []
    for path in _result_paths(config, cwd):
        if not path.is_file():
            return None
        stat = path.stat()
        if stat.st_size <= 0:
            return None
        signature.append({"name": path.name, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    return signature


def _write_completion_marker(config: SimulationConfig, cwd: Path, signature) -> None:
    marker = _completion_marker_path(config, cwd)
    temporary_marker = marker.with_suffix(marker.suffix + ".tmp")
    payload = {
        "version": 1,
        "config_name": config.config_name,
        "ini_file": config.ini_file,
        "results": signature,
    }
    temporary_marker.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary_marker, marker)


def _has_complete_results(config: SimulationConfig, cwd: Path) -> bool:
    marker = _completion_marker_path(config, cwd)
    signature = _result_signature(config, cwd)
    if signature is None or not marker.is_file():
        return False

    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    return (
        payload.get("version") == 1
        and payload.get("config_name") == config.config_name
        and payload.get("ini_file") == config.ini_file
        and payload.get("results") == signature
    )


def _clean_result_files(config: SimulationConfig, cwd: Path) -> None:
    results_dir = cwd / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    for stale_file in results_dir.glob(config.config_name + "*"):
        if stale_file.is_file():
            stale_file.unlink(missing_ok=True)


def _register_process(process: subprocess.Popen) -> None:
    _ACTIVE_SIMULATION_PROCESSES[process.pid] = process


def _unregister_process(process: subprocess.Popen) -> None:
    _ACTIVE_SIMULATION_PROCESSES.pop(process.pid, None)


def _process_group_exists(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return False


def _terminate_process_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError:
        if process.poll() is None:
            process.terminate()
    else:
        deadline = time.monotonic() + _PROCESS_GROUP_TERMINATION_GRACE_SECONDS
        while _process_group_exists(process.pid) and time.monotonic() < deadline:
            process.poll()
            time.sleep(0.1)
        if _process_group_exists(process.pid):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                if process.poll() is None:
                    process.kill()

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    finally:
        _unregister_process(process)


def _terminate_active_process_groups() -> None:
    for process in list(_ACTIVE_SIMULATION_PROCESSES.values()):
        _terminate_process_group(process)


def _handle_shutdown_signal(signum, _frame) -> None:
    raise SystemExit(128 + signum)


def _install_shutdown_signal_handlers():
    previous_handlers = {}
    for signal_name in ("SIGTERM", "SIGHUP"):
        shutdown_signal = getattr(signal, signal_name, None)
        if shutdown_signal is None:
            continue
        previous_handlers[shutdown_signal] = signal.getsignal(shutdown_signal)
        signal.signal(shutdown_signal, _handle_shutdown_signal)
    return previous_handlers


def _restore_signal_handlers(previous_handlers) -> None:
    for shutdown_signal, previous_handler in previous_handlers.items():
        signal.signal(shutdown_signal, previous_handler)


def _env_int(name: str, default: int) -> int:
    value = int(os.environ.get(name, str(default)))
    if value < 0:
        raise ValueError(f"{name} must not be negative")
    return value


def _env_float(name: str, default: float) -> float:
    value = float(os.environ.get(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _logs_dir(cwd: Path) -> Path:
    logs_dir = cwd.parents[1] / "logs" / cwd.name / "simulations"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _start_simulation(config: SimulationConfig, cwd: Path, attempt: int) -> _RunningSimulation:
    _clean_result_files(config, cwd)
    command = build_simulation_command(
        config.protocol,
        config.ini_file,
        config.config_name,
        include_leo=config.include_leo,
    )
    log_path = None
    log_file = None
    logs_dir = cwd.parents[1] / "logs" / cwd.name / "simulations"
    if attempt == 1 and logs_dir.is_dir():
        for stale_log in logs_dir.glob(f"{config.config_name}.attempt*.log"):
            stale_log.unlink(missing_ok=True)
    elif attempt > 1:
        log_path = _logs_dir(cwd) / f"{config.config_name}.attempt{attempt}.log"
        log_file = log_path.open("w", encoding="utf-8")
        log_file.write("$ " + " ".join(command) + "\n\n")
        log_file.flush()

    output_kwargs = simulation_output_kwargs(config.protocol)
    if log_file is not None:
        output_kwargs = {"stdout": log_file, "stderr": subprocess.STDOUT}

    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            start_new_session=True,
            **output_kwargs,
        )
    except BaseException:
        if log_file is not None:
            log_file.close()
        raise
    _register_process(process)
    return _RunningSimulation(config, process, time.monotonic(), log_file, log_path)


def _finish_simulation(
    running: _RunningSimulation,
    cwd: Path,
    timeout_seconds: float,
    runtime_file,
) -> bool:
    elapsed = time.monotonic() - running.started
    timed_out = False
    try:
        return_code = running.process.wait(timeout=max(0, timeout_seconds - elapsed))
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process_group(running.process)
        return_code = running.process.returncode
    else:
        _unregister_process(running.process)

    elapsed = time.monotonic() - running.started
    signature = _result_signature(running.config, cwd)
    complete = not timed_out and return_code == 0 and signature is not None
    marker_error = None
    if complete:
        try:
            _write_completion_marker(running.config, cwd, signature)
        except OSError as error:
            complete = False
            marker_error = error
    if timed_out:
        status = f"timed out after {elapsed:.1f}s"
    elif return_code != 0:
        status = f"failed with exit code {return_code}"
    elif marker_error is not None:
        status = f"finished but could not record completion: {marker_error}"
    elif not complete:
        status = "finished without complete vec/sca output"
    else:
        status = f"complete in {elapsed:.1f}s"

    if running.log_file is not None:
        running.log_file.write(f"\n{status}\n")
        running.log_file.close()
    if runtime_file is not None:
        runtime_file.write(f"\n{running.config.config_name}: {status}")
        runtime_file.flush()
    print(f"  {running.config.config_name}: {status}")
    if not complete:
        if running.log_path is None:
            print("    first-attempt output was suppressed; retry output will be logged")
        else:
            print(f"    log: {running.log_path}")
    return complete


def run_simulation_configs(configs, cwd, cores: int, runtime_file=None) -> None:
    previous_handlers = _install_shutdown_signal_handlers()
    try:
        _run_simulation_configs(configs, cwd, cores, runtime_file)
    finally:
        _terminate_active_process_groups()
        _restore_signal_handlers(previous_handlers)


def _run_simulation_configs(configs, cwd, cores: int, runtime_file=None) -> None:
    cwd = Path(cwd).resolve()
    timeout_seconds = _env_float("EXPERIMENT_SIM_TIMEOUT_SECONDS", 2.5 * 60 * 60)
    retries = _env_int("EXPERIMENT_RETRIES", 3)
    retry_delay_seconds = _env_float("EXPERIMENT_RETRY_DELAY_SECONDS", 1)
    resume = os.environ.get("EXPERIMENT_RESUME", "").lower() in {"1", "true", "yes", "on"}
    cores = max(1, int(cores))
    pending = [config for config in configs if not (resume and _has_complete_results(config, cwd))]
    skipped = len(configs) - len(pending)

    if skipped:
        print(f"Skipping {skipped} config(s) with verified completion markers because EXPERIMENT_RESUME is enabled.")

    attempts = retries + 1
    for attempt in range(1, attempts + 1):
        if not pending:
            return

        print(
            f"\nRunning {len(pending)} simulation config(s), attempt {attempt}/{attempts}, "
            f"up to {cores} at a time with a {timeout_seconds:g}s timeout.\n"
        )
        failed = []
        remaining = iter(pending)
        running_simulations = []

        try:
            while True:
                # Keep the requested number of simulations live. A completed job
                # immediately frees a slot for the next configuration.
                while len(running_simulations) < cores:
                    try:
                        config = next(remaining)
                    except StopIteration:
                        break
                    running_simulations.append(_start_simulation(config, cwd, attempt))
                    print(f"  started: {config.config_name}")

                if not running_simulations:
                    break

                completed = []
                now = time.monotonic()
                for running in running_simulations:
                    timed_out = now - running.started >= timeout_seconds
                    if timed_out or running.process.poll() is not None:
                        completed.append(running)

                if not completed:
                    time.sleep(0.05)
                    continue

                for running in completed:
                    running_simulations.remove(running)
                    if not _finish_simulation(running, cwd, timeout_seconds, runtime_file):
                        failed.append(running.config)
        except BaseException:
            for running in running_simulations:
                _terminate_process_group(running.process)
                if running.log_file is not None and not running.log_file.closed:
                    running.log_file.write("\nterminated because the run was interrupted\n")
                    running.log_file.close()
            raise

        pending = failed
        if pending and attempt < attempts:
            print(f"\nRetrying {len(pending)} failed or incomplete simulation config(s).\n")
            time.sleep(retry_delay_seconds)

    if not pending:
        return

    missing = "\n".join(f"  {config.config_name}" for config in pending)
    raise RuntimeError(f"Simulation outputs are still incomplete after {attempts} attempt(s):\n{missing}")


def _ensure_ned_path(text: str, include_leo: bool) -> str:
    first_config = text.find("\n[Config ")
    general_text = text if first_config == -1 else text[:first_config]
    if "ned-path" in general_text:
        return text
    return text.replace("[General]\n", "[General]\n" + common_ned_path(include_leo) + "\n", 1)


def _ensure_load_libs(text: str) -> str:
    if not ide_load_libs_enabled():
        return text
    first_config = text.find("\n[Config ")
    general_text = text if first_config == -1 else text[:first_config]
    if "load-libs" in general_text:
        return text
    return text.replace("[General]\n", "[General]\n" + common_load_libs() + "\n", 1)


def _raynet_parameter_lines(protocol: str):
    protocol = protocol.lower()
    lines = [
        "",
        "# RayNet protocol settings",
        "**.printDebugMessages = false",
        "**.takeActions = true",
    ]
    if protocol == "astrea":
        lines.extend(
            [
                "**.maxWindow = 10",
                "**.stateSize = 4",
                "**.maxObsCount = 15",
                "**.ewmaWeight = 1.5",
                "**.rewardDelayForgiveness = 1.25",
                "**.rewardLossMultiplier = 5",
                "**.maxRLSteps = 100000",
                "**.monitorIntervalDuration = 1.0",
                '**.broker.obsCollectionMode = "GROUPED"',
            ]
        )
    else:
        lines.extend(
            [
                "**.maxRLSteps = 0",
                "**.fixedIntervals = true",
                "**.fixedIntervalDuration = 0.02",
            ]
        )
    return lines


def _insert_raynet_parameters(text: str, protocol: str) -> str:
    marker = "\n[Config "
    insertion = "\n".join(_raynet_parameter_lines(protocol)) + "\n"
    if marker in text:
        return text.replace(marker, "\n" + insertion + marker, 1)
    return text + "\n" + insertion


def _ensure_orca_receiver_tcp(text: str) -> str:
    receiver_lines = (
        '**.server[*].tcp.typename = "TcpPaced"',
        '**.server[*].tcp.tcpAlgorithmClass = "TcpCubic"',
    )
    if all(line in text for line in receiver_lines):
        return text

    marker = '\n**.tcp.typename = "'
    if marker not in text:
        raise ValueError("Cannot insert RayNet receiver TCP settings: missing TCP typename assignment")

    insertion = "\n".join(receiver_lines) + "\n"
    return text.replace(marker, "\n" + insertion + marker.lstrip("\n"), 1)


def clone_raynet_ini_variants(base_ini_path, source_protocol: str = "bbr", include_leo: bool = False):
    base_ini = Path(base_ini_path)
    if not base_ini.exists():
        print(f"Warning: cannot generate RayNet variants; missing base ini {base_ini}")
        return

    source_display = protocol_config_prefix(source_protocol)
    source_name = f"_{source_protocol}"
    source_text = base_ini.read_text(encoding="utf-8")

    for protocol in RAYNET_PROTOCOLS:
        tcp_type, alg_class = RAYNET_ALG_FLAVOUR[protocol]
        display = protocol_config_prefix(protocol)
        target_name = base_ini.name.replace(source_name, f"_{protocol}", 1)
        target_ini = base_ini.with_name(target_name)

        text = source_text
        text = text.replace('**.tcp.typename = "Bbr"', f'**.tcp.typename = "{tcp_type}"')
        text = text.replace('**.tcp.tcpAlgorithmClass = "BbrFlavour"', f'**.tcp.tcpAlgorithmClass = "{alg_class}"')
        text = text.replace(source_display, display)
        if protocol == "orca":
            text = _ensure_orca_receiver_tcp(text)
        text = _ensure_ned_path(text, include_leo)
        text = _ensure_load_libs(text)
        text = _insert_raynet_parameters(text, protocol)
        target_ini.write_text(text, encoding="utf-8")
        print(f"Generated RayNet ini file {target_ini}")


def raynet_alias_section(protocol: str) -> str | None:
    return _RAYNET_CONFIG_ALIAS.get(protocol.lower())
