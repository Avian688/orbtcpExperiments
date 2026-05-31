#!/usr/bin/env python3

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd


VECTOR_NAMES = ("goodput", "rtt")


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
    return np.fromstring(value, sep=" ") if value else None


def vectors_from(file_path: Path):
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


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: extractSingleCsvFile.py <CSV-R file> <protocol> <run>")

    input_file = Path(sys.argv[1])
    protocol = sys.argv[2]
    run = int(sys.argv[3])
    out_root = Path("../../paperExperiments/experiment12/csvs") / protocol / f"run{run}"
    vectors = vectors_from(input_file)

    for vector_name in VECTOR_NAMES:
        matching_vectors = vectors[vectors["name"] == f"{vector_name}:vector(removeRepeats)"]
        for _, row in matching_vectors.iterrows():
            if row.vecvalue is None:
                continue
            module_name = sanitise_module_name(row.module)
            out_dir = out_root / module_name
            out_dir.mkdir(parents=True, exist_ok=True)
            pd.DataFrame({"time": row.vectime, vector_name: row.vecvalue}).to_csv(
                out_dir / f"{vector_name}.csv",
                index=False,
            )


if __name__ == "__main__":
    main()
