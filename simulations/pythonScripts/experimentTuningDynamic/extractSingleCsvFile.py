#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

from experimentTuningDynamicSupport import EXPERIMENT


VECTOR_NAMES = ("goodput", "queueLength", "retransmissionRate")


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
    if len(sys.argv) != 6:
        raise SystemExit(
            "Usage: extractSingleCsvFile.py "
            "<CSV-R file> <variant> <condition> <flow-count> <run>"
        )

    input_file = Path(sys.argv[1])
    variant = sys.argv[2]
    condition = sys.argv[3]
    flow_count = int(sys.argv[4])
    run = int(sys.argv[5])
    out_root = (
        Path("../../paperExperiments")
        / EXPERIMENT
        / "csvs"
        / variant
        / condition
        / f"{flow_count}flows"
        / f"run{run}"
    )
    vectors = vectors_from(input_file)

    for name in VECTOR_NAMES:
        matching_vectors = vectors[vectors["name"].map(vector_name) == name]
        for _, row in matching_vectors.iterrows():
            times = row.vectime
            values = row.vecvalue
            sample_count = min(len(times), len(values))
            if sample_count == 0:
                continue

            module_name = sanitise_module_name(row.module)
            out_dir = out_root / module_name
            out_dir.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(
                {"time": times[:sample_count], name: values[:sample_count]}
            ).to_csv(out_dir / f"{name}.csv", index=False)


if __name__ == "__main__":
    main()
