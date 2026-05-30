#!/usr/bin/env python3

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def parse_if_number(value):
    try:
        return float(value)
    except Exception:
        if value == "true":
            return True
        if value == "false":
            return False
        return value if value else None


def parse_ndarray(value):
    return np.fromstring(value, sep=" ") if value else None


def get_results(file_path: Path) -> pd.DataFrame:
    results_file = pd.read_csv(
        file_path,
        converters={
            "attrvalue": parse_if_number,
            "binedges": parse_ndarray,
            "binvalues": parse_ndarray,
            "vectime": parse_ndarray,
            "vecvalue": parse_ndarray,
        },
    )
    return results_file[results_file.type == "vector"]


def normalized_module_name(module_name: str) -> str:
    if "thread" in module_name:
        module_name = re.sub(r"\.thread_\d+", "", module_name)
    return re.sub(r"(conn)-\d+", r"\1", module_name)


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: extractSingleCsvFile.py <scavetool_csv> <variant_key> <run>")
        return 2

    file_path = Path(sys.argv[1])
    variant_key = sys.argv[2]
    run = int(sys.argv[3])

    raw_results = get_results(file_path)
    cwnd_results = raw_results.loc[raw_results["name"] == "cwnd:vector(removeRepeats)"]
    out_root = Path("../../paperExperiments/experiment0/csvs") / variant_key / f"run{run}"
    extracted = False

    for _, row in cwnd_results.iterrows():
        values = row["vecvalue"]
        times = row["vectime"]
        if values is None or times is None:
            continue

        module_path = out_root / normalized_module_name(str(row["module"]))
        module_path.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"time": times, "cwnd": values}).to_csv(module_path / "cwnd.csv", index=False)
        extracted = True

    if not extracted:
        print(f"No cwnd vectors found in {file_path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
