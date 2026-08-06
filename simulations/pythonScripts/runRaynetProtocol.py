#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from raynetExperimentSupport import RAYNET_HOME, raynet_alias_section


def materialize_headless_ini(protocol: str, ini_path: Path, config_name: str) -> Path:
    alias = raynet_alias_section(protocol)
    text = ini_path.read_text(encoding="utf-8")
    general_marker = "[General]\n"
    if general_marker not in text:
        raise ValueError(f"Missing [General] section in {ini_path}")

    text = text.replace(
        general_marker,
        general_marker + '*.visualizer.typename = ""\n',
        1,
    )
    generated = ini_path.with_name(f".{ini_path.stem}.{protocol}.{os.getpid()}{ini_path.suffix}")
    if alias is not None:
        text = (
            text.rstrip()
            + f"\n\n[Config {alias}]\n"
            + f"extends = {config_name}\n"
            + f'output-vector-file = "results/{config_name}-#0.vec"\n'
            + f'output-scalar-file = "results/{config_name}-#0.sca"\n'
        )
    generated.write_text(text, encoding="utf-8")
    return generated


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: runRaynetProtocol.py <protocol> <ini_path> <section>")
        return 2

    protocol = sys.argv[1].lower()
    ini_path = Path(sys.argv[2]).expanduser()
    if not ini_path.is_absolute():
        ini_path = Path.cwd() / ini_path
    ini_path = ini_path.resolve(strict=False)
    section = sys.argv[3]

    prepared_ini = materialize_headless_ini(protocol, ini_path, section)
    raynet_python = RAYNET_HOME / ".venv" / "bin" / "python"
    raynet_runner = RAYNET_HOME / "_scripts" / "run" / "raynet_runner.py"

    command = [
        str(raynet_python),
        str(raynet_runner),
        protocol,
        str(prepared_ini),
        section,
    ]
    try:
        return subprocess.run(command).returncode
    finally:
        if prepared_ini != ini_path:
            prepared_ini.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
