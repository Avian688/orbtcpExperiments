#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAYNET_PROTOCOLS = ("orca")#, "cleanslate", "astrea")

RAYNET_ALG_FLAVOUR = {
    "orca": ("OrcaTcp", "Orca"),
    "cleanslate": ("CleanSlateTcp", "CleanSlate"),
    "astrea": ("AstreaTcp", "Astrea"),
}

_RAYNET_CONFIG_ALIAS = {
    "cleanslate": "CleanSlate",
    "astrea": "Astrea",
}

RAYNET_HOME = Path(os.environ.get("RAYNET_HOME", Path.home() / "raynet")).expanduser()

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
    RAYNET_HOME / "simlibs" / "RLComponents" / "src",
    RAYNET_HOME / "simlibs" / "Orca" / "src",
    RAYNET_HOME / "simlibs" / "CleanSlate" / "src",
    RAYNET_HOME / "simlibs" / "Astrea" / "src",
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


def protocol_config_prefix(protocol: str) -> str:
    return protocol.title()


def common_ned_path(include_leo: bool = False) -> str:
    paths = list(BASE_NED_PATHS)
    if include_leo:
        paths.extend(LEO_NED_PATHS)
    paths.extend(str(path) for path in RAYNET_NED_PATHS)
    return "ned-path = " + ":".join(paths)


def build_opp_run_command(config_name: str, ini_file: str, include_leo: bool = False):
    ned_paths = list(BASE_NED_PATHS)
    if include_leo:
        ned_paths.extend(LEO_NED_PATHS)
    ned_paths.append(str(RAYNET_HOME / "simlibs" / "RLComponents" / "src"))

    image_path = "../../../../inet4.5/images"
    if include_leo:
        image_path += ":../../../../os3/images"

    libs = list(BASE_LIBS)
    if include_leo:
        libs.extend(LEO_LIBS)
    libs.append(str(RAYNET_HOME / "simlibs" / "RLComponents" / "src" / "RLComponents"))

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


def _ensure_ned_path(text: str, include_leo: bool) -> str:
    first_config = text.find("\n[Config ")
    general_text = text if first_config == -1 else text[:first_config]
    if "ned-path" in general_text:
        return text
    return text.replace("[General]\n", "[General]\n" + common_ned_path(include_leo) + "\n", 1)


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
        text = _ensure_ned_path(text, include_leo)
        text = _insert_raynet_parameters(text, protocol)
        target_ini.write_text(text, encoding="utf-8")
        print(f"Generated RayNet ini file {target_ini}")


def raynet_alias_section(protocol: str) -> str | None:
    return _RAYNET_CONFIG_ALIAS.get(protocol.lower())
