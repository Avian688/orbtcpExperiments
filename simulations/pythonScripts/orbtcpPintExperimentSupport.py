#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path

from raynetExperimentSupport import ensure_local_ini_preamble


_ORBTCP_FLAVOUR = '**.tcp.tcpAlgorithmClass = "OrbtcpFlavour"'
_PINT_FLAVOUR = '**.tcp.tcpAlgorithmClass = "OrbtcpPintFlavour"'
_CONFIG_HEADER = re.compile(r"(?m)^(\[Config )Orbtcp")
_LEO_NETWORK = re.compile(r"(?m)^network\s*=\s*(?:[\w.]+\.)?leoconstellation\s*$")
_UNITLESS_FIXED_RTT = re.compile(
    r"(?m)^(\*\*\.fixedAvgRTTVal\s*=\s*)([+-]?(?:\d+(?:\.\d*)?|\.\d+))(\s*)$"
)

_PINT_PARAMETER_LINES = (
    "",
    "# OrbCC-PINT approximation settings",
    "# Full feedback isolates quantization and sketch effects from feedback sampling.",
    "**.tcp.pintFeedbackProbability = 1",
    "**.**.queue.pintInitialRtt = 10ms",
    "**.**.queue.flowCardinalityBits = 4096",
    "**.**.queue.flowSketchSeed = 1337",
    "**.**.queue.pintBits = 8",
    "**.**.queue.pintLogBase = 1.05",
    "**.**.queue.pintMaxConcurrentFlows = 512",
    "",
)


def _is_orbtcp_source(path: Path) -> bool:
    if "_orbtcp_pint" in path.stem or "_orbtcp" not in path.stem:
        return False

    suffix = path.stem.split("_orbtcp", 1)[1]
    return suffix == "" or (suffix.startswith("_") and suffix.endswith("buffer"))


def _target_path(source: Path) -> Path:
    return source.with_name(source.name.replace("_orbtcp", "_orbtcp_pint", 1))


def _validate_transformed_ini(source: Path, source_text: str, pint_text: str) -> None:
    source_configs = len(re.findall(r"(?m)^\[Config ", source_text))
    pint_configs = len(re.findall(r"(?m)^\[Config OrbtcpPint", pint_text))
    if source_configs != pint_configs:
        raise ValueError(
            f"{source} has {source_configs} source configs but {pint_configs} PINT configs"
        )

    stale_names = ("OrbtcpFlavour", "IntQueue", "IntInterface")
    if any(name in pint_text for name in stale_names):
        raise ValueError(f"{source} retained a base OrbCC class or module name")

    for section in re.split(r"(?m)(?=^\[(?:General|Config )[^\n]*\]$)", pint_text):
        pint_queue = section.find('queue.typename = "PintQueue"')
        fallback = section.find('**.**.queue.typename = "DropTailQueue"')
        if pint_queue != -1 and fallback != -1 and pint_queue > fallback:
            raise ValueError(
                f"{source} selects PintQueue after the DropTailQueue fallback"
            )


def _transform_ini(source: Path) -> str:
    source_text = source.read_text(encoding="utf-8")

    if source_text.count(_ORBTCP_FLAVOUR) != 1:
        raise ValueError(
            f"{source} must contain exactly one {_ORBTCP_FLAVOUR!r} assignment"
        )
    if '"IntQueue"' not in source_text:
        raise ValueError(f"{source} does not select an IntQueue")
    if not _CONFIG_HEADER.search(source_text):
        raise ValueError(f"{source} does not contain an OrbTCP config section")

    text = source_text
    text = ensure_local_ini_preamble(
        text,
        include_leo=bool(_LEO_NETWORK.search(source_text)),
    )
    text = text.replace(
        _ORBTCP_FLAVOUR,
        _PINT_FLAVOUR + "\n" + "\n".join(_PINT_PARAMETER_LINES),
        1,
    )
    text = text.replace("IntQueue", "PintQueue")
    text = text.replace("IntInterface", "PintInterface")
    text = _CONFIG_HEADER.sub(r"\1OrbtcpPint", text)
    text, fixed_rtt_replacements = _UNITLESS_FIXED_RTT.subn(
        lambda match: f"{match.group(1)}{match.group(2)}s{match.group(3)}",
        text,
    )
    if fixed_rtt_replacements != 1:
        raise ValueError(
            f"{source} must contain exactly one unitless fixedAvgRTTVal assignment"
        )

    source_header = (
        f"# Generated from {source.name} by orbtcpPintExperimentSupport.py.\n"
        "# Regenerate this file instead of editing it directly.\n\n"
    )
    pint_text = source_header + text
    _validate_transformed_ini(source, source_text, pint_text)
    return pint_text


def clone_orbtcp_pint_ini_variants(
    experiment_dir: str | Path, *, check: bool = False
) -> list[Path]:
    experiment_dir = Path(experiment_dir)
    sources = [
        path
        for path in sorted(experiment_dir.glob("experiment*_orbtcp*.ini"))
        if _is_orbtcp_source(path)
    ]

    if not sources:
        raise FileNotFoundError(
            f"No base OrbTCP INI files found in {experiment_dir}"
        )

    stale_targets = []
    targets = []
    for source in sources:
        target = _target_path(source)
        expected = _transform_ini(source)
        targets.append(target)

        if target.exists() and target.read_text(encoding="utf-8") == expected:
            continue
        if check:
            stale_targets.append(target)
            continue

        target.write_text(expected, encoding="utf-8")
        print(f"Generated OrbCC-PINT ini file {target}")

    if stale_targets:
        formatted = "\n".join(f"  {path}" for path in stale_targets)
        raise RuntimeError(f"OrbCC-PINT INI files are missing or stale:\n{formatted}")

    return targets


def _paper_experiments_root() -> Path:
    return Path(__file__).resolve().parents[1] / "paperExperiments"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate standalone OrbCC-PINT INIs from OrbCC experiment INIs."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if a generated INI is missing or differs from its OrbCC source.",
    )
    args = parser.parse_args()

    generated = []
    for experiment_dir in sorted(_paper_experiments_root().glob("experiment[0-9]*")):
        if not experiment_dir.is_dir():
            continue
        if not any(_is_orbtcp_source(path) for path in experiment_dir.glob("*.ini")):
            continue
        generated.extend(
            clone_orbtcp_pint_ini_variants(experiment_dir, check=args.check)
        )

    action = "Validated" if args.check else "Prepared"
    print(f"{action} {len(generated)} OrbCC-PINT INI file(s).")


if __name__ == "__main__":
    main()
