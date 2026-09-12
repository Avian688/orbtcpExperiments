#!/usr/bin/env python3
"""Create isolated source/input snapshots; never copy results or run simulations."""

import ast
from pathlib import Path
import re


SCRIPT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_ROOT.parents[1]
PAPER_ROOT = PROJECT_ROOT / "simulations/paperExperiments"
EXPERIMENTS = tuple(f"experiment{i}" for i in (*range(1, 12), 13))
SHARED = (
    "orbtcpPintExperimentSupport", "raynetExperimentSupport", "plotDataExport",
    "plotHeaderLines", "plotHeaderLinesSymbol", "plotProtocolSupport",
    "runPlotVariants", "runRaynetProtocol",
)
REPLACEMENTS = {
    name: name + "FrontTail"
    for name in (*EXPERIMENTS, "experiment1and2", *SHARED)
}
REPLACEMENTS.update({
    name[0].upper() + name[1:]: name[0].upper() + name[1:] + "FrontTail"
    for name in (*EXPERIMENTS, "experiment1and2")
})
REPLACEMENTS.update({
    "BandwidthRecorderDropTailQueue": "BandwidthRecorderFrontTailQueue",
    "DropTailQueue": "DropHeadQueue",
    "IntQueue": "IntFrontTailQueue",
    "PintQueue": "PintFrontTailQueue",
    "IntInterface": "IntFrontTailInterface",
    "PintInterface": "PintFrontTailInterface",
    "PacketAtCollectionEndDropper": "PacketAtCollectionBeginDropper",
})
PATTERN = re.compile("|".join(re.escape(key) for key in sorted(
    REPLACEMENTS, key=len, reverse=True
)))


def transform(text):
    return PATTERN.sub(lambda match: REPLACEMENTS[match.group()], text)


def transform_source(source):
    text = transform(source.read_text())
    # Routing snapshots describe topology, not queue admission. Reuse the
    # original corpus for loading only; keep all simulation outputs isolated.
    text = text.replace('configLocation = "../experiment8FrontTail/"',
                        'configLocation = "../experiment8/"')
    if source.name == "generateExperiment8IniFile.py":
        text = text.replace('os.environ.get("LEO_ROUTING_CORPUS_ROOT", "")',
                            'os.environ.get("LEO_ROUTING_CORPUS_ROOT", "../experiment8/")')
    if source.suffix == ".ini" and source.parent.name == "experiment8":
        if "configLocation" not in text:
            text = text.replace("[General]", '[General]\n*.configurator.configLocation = "../experiment8/"', 1)
    if source.name == "orbtcpPintExperimentSupport.py":
        text = text.replace('glob("experiment[0-9]*")',
                            'glob("experiment[0-9]*FrontTail")')
    if source.name == "raynetExperimentSupport.py":
        text = text.replace(
            "available = with_experiment_protocols(default_protocols)",
            'available = [p for p in with_experiment_protocols(default_protocols)\n'
            '                 if p in {"orbtcp_pint", "cubic", "bbr3", "leocc", "satcp"}]',
        )
    if source.name == "plotProtocolSupport.py":
        start = text.index("def _select_protocols(")
        end = text.index("\ndef _validate_protocol_sets", start)
        text = text[:start] + (
            'def _select_protocols(final_protocols, comparison_protocols):\n'
            '    return [p for p in final_protocols\n'
            '            if p in {"orbtcp_pint", "cubic", "bbr3", "leocc", "satcp"}]\n\n'
        ) + text[end:]
    if source.name == "runPlotVariants.py":
        start = text.index("    before_main = snapshot_files(cwd)")
        end = text.index('\n\nif __name__', start)
        text = text[:start] + (
            '    run_plot(script, args.script_args, cwd, MAIN_VARIANT, WITHOUT_BBRV1)\n'
            '    return 0\n'
        ) + text[end:]
    return text


def sources():
    for name in EXPERIMENTS:
        for path in (SCRIPT_ROOT / name).glob("*"):
            if path.suffix in {".py", ".csv", ".sh"} and path.is_file():
                yield path
        for path in (PAPER_ROOT / name).glob("*"):
            if path.suffix in {".ned", ".ini", ".xml", ".csv"} and path.is_file():
                yield path
        for category in (
            "scenarios", "bandwidths", "baseRtts", "setupInformation", "startTimes"
        ):
            for path in (PAPER_ROOT / category / name).rglob("*"):
                if path.is_file() and path.suffix in {".xml", ".json", ".csv"}:
                    yield path
    for name in SHARED:
        yield SCRIPT_ROOT / (name + ".py")


def main():
    outputs = {}
    for source in sources():
        relative = source.relative_to(PROJECT_ROOT)
        target = PROJECT_ROOT / transform(str(relative))
        if source == target:
            raise RuntimeError(f"Refusing to overwrite an original: {source}")
        text = transform_source(source)
        if target.suffix == ".py":
            ast.parse(text, filename=str(target))
        outputs[target] = text

    # These compound modules fix their queue type, so typename overrides alone
    # cannot select the new telemetry queues.
    orb_root = PROJECT_ROOT.parent / "orbtcp/src/linklayer/ppp"
    for name in ("IntInterface", "PintInterface"):
        source = orb_root / (name + ".ned")
        outputs[orb_root / (REPLACEMENTS[name] + ".ned")] = transform(source.read_text())

    conflicts = [path for path, text in outputs.items()
                 if path.exists() and path.read_text() != text]
    if conflicts:
        raise RuntimeError("Existing FrontTail files differ; refusing to replace them: "
                           + ", ".join(str(path) for path in conflicts[:10]))
    for path, text in outputs.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(f"Prepared {len(outputs)} FrontTail source/input files; no simulations run.")


if __name__ == "__main__":
    main()
