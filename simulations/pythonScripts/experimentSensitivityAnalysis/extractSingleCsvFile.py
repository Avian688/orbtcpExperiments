#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

from experimentSensitivityAnalysisSupport import EXPERIMENT


VECTOR_NAMES = (
    "goodput",
    "retransmissionRate",
    "persistentQueueingDelay",
    "numberOfFlows",
    "numOfFlowsInInitialPhase",
    "pintLocalUtilization",
    "pintDecodedUtilization",
)


def parse_if_number(value):
    try:
        return float(value)
    except ValueError:
        if value == "true":
            return True
        if value == "false":
            return False
        return value or None


def parse_ndarray(value):
    return np.fromstring(value, sep=" ") if value else np.asarray([])


def vectors_from(file_path: Path) -> pd.DataFrame:
    results = pd.read_csv(
        file_path,
        converters={
            "attrvalue": parse_if_number,
            "binedges": parse_ndarray,
            "binvalues": parse_ndarray,
            "vectime": parse_ndarray,
            "vecvalue": parse_ndarray,
        },
    )
    return results[results.type == "vector"]


def sanitise_module_name(module_name: str) -> str:
    module_name = re.sub(r"\.thread_\d+", "", module_name)
    return re.sub(r"(conn)-\d+", r"\1", module_name)


def vector_name(name: str) -> str:
    return str(name).split(":", 1)[0]


def main() -> None:
    if len(sys.argv) != 7:
        raise SystemExit(
            "Usage: extractSingleCsvFile.py <CSV-R file> <experiment-key> "
            "<variant> <condition> <workload> <run>"
        )

    input_file = Path(sys.argv[1])
    experiment_key = sys.argv[2]
    variant = sys.argv[3]
    condition = sys.argv[4]
    workload = sys.argv[5]
    run = int(sys.argv[6])
    out_root = (
        Path("../../paperExperiments")
        / EXPERIMENT
        / "csvs"
        / experiment_key
        / variant
        / condition
        / workload
        / f"run{run}"
    )
    vectors = vectors_from(input_file)

    written = 0
    for name in VECTOR_NAMES:
        matching_vectors = vectors[vectors["name"].map(vector_name) == name]
        for _, row in matching_vectors.iterrows():
            times = row.vectime
            values = row.vecvalue
            sample_count = min(len(times), len(values))
            if sample_count == 0:
                continue

            module_name = sanitise_module_name(str(row.module))
            out_dir = out_root / module_name
            out_dir.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(
                {"time": times[:sample_count], name: values[:sample_count]}
            ).to_csv(out_dir / f"{name}.csv", index=False)
            written += 1

    if written == 0:
        raise RuntimeError(f"No required vectors found in {input_file}")


if __name__ == "__main__":
    main()
