#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from experimentSensitivityAnalysisSupport import (
    EXPERIMENT,
    PINT_MAX_CONCURRENT_FLOWS,
    PINT_MAX_FLOW_COUNT,
    PINT_MAX_UTILIZATION,
    SELECTED_FLOW_COUNT_BITS,
    SELECTED_SKETCH_BITS,
    SELECTED_UTILIZATION_BITS,
    SYNTHETIC_BITMAP_BITS,
    SYNTHETIC_ENCODING_BITS,
    SYNTHETIC_HASH_SEEDS,
    SYNTHETIC_ID_PATTERNS,
    SYNTHETIC_MAX_FLOWS,
)


SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = (
    SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT / "synthetic"
).resolve()
UINT64_MASK = np.uint64(0xFFFFFFFFFFFFFFFF)
HASH_SALT = np.uint64(0xD6E8FEB86659FD93)


def mix_hash(values: np.ndarray) -> np.ndarray:
    """Vectorized port of PintQueue::mixHash using uint64 wraparound."""
    values = np.asarray(values, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        values += np.uint64(0x9E3779B97F4A7C15)
        values = (values ^ (values >> np.uint64(30))) * np.uint64(
            0xBF58476D1CE4E5B9
        )
        values = (values ^ (values >> np.uint64(27))) * np.uint64(
            0x94D049BB133111EB
        )
    return (values ^ (values >> np.uint64(31))) & UINT64_MASK


def flow_ids(pattern: str) -> np.ndarray:
    sequential = np.arange(1, SYNTHETIC_MAX_FLOWS + 1, dtype=np.uint64)
    if pattern == "sequential":
        return sequential
    if pattern == "random64":
        return mix_hash(sequential ^ np.uint64(0xA0761D6478BD642F))
    raise ValueError(f"Unknown flow-ID pattern: {pattern}")


def flow_count_checkpoints() -> tuple[int, ...]:
    values = {1 << exponent for exponent in range(17)}
    values.update((5, 20, 31, 32, 64, 100, 127, 128, 256, 512, 1000))
    return tuple(sorted(value for value in values if value <= SYNTHETIC_MAX_FLOWS))


def linear_counting_rows() -> list[dict[str, float | int | str | bool]]:
    checkpoints = flow_count_checkpoints()
    rows = []
    for pattern in SYNTHETIC_ID_PATTERNS:
        ids = flow_ids(pattern)
        insertion_indexes = np.arange(len(ids), dtype=np.int64)
        for seed_index in range(SYNTHETIC_HASH_SEEDS):
            sketch_seed = np.uint64(1337 + seed_index * 7919)
            hashes = mix_hash(ids ^ sketch_seed ^ HASH_SALT)
            for bitmap_bits in SYNTHETIC_BITMAP_BITS:
                positions = (hashes % np.uint64(bitmap_bits)).astype(np.int64)
                first_seen = np.full(bitmap_bits, len(ids), dtype=np.int64)
                np.minimum.at(first_seen, positions, insertion_indexes)

                for true_count in checkpoints:
                    set_bits = int(np.count_nonzero(first_seen < true_count))
                    zero_bits = bitmap_bits - set_bits
                    if zero_bits == bitmap_bits:
                        estimate = 0.0
                    elif zero_bits == 0:
                        estimate = bitmap_bits * math.log(bitmap_bits)
                    else:
                        estimate = -bitmap_bits * math.log(
                            zero_bits / bitmap_bits
                        )
                    relative_error = (estimate - true_count) / true_count
                    rows.append(
                        {
                            "id_pattern": pattern,
                            "hash_seed": int(sketch_seed),
                            "bitmap_bits": bitmap_bits,
                            "true_count": true_count,
                            "set_bits": set_bits,
                            "zero_bits": zero_bits,
                            "estimated_count": estimate,
                            "relative_error": relative_error,
                            "absolute_relative_error": abs(relative_error),
                            "saturated": zero_bits == 0,
                            "state_bytes_four_banks": bitmap_bits // 2,
                        }
                    )
    return rows


def flow_count_max_code(bits: int) -> int:
    return PINT_MAX_FLOW_COUNT if bits == 0 else (1 << bits) - 1


def flow_count_exact_max(bits: int, max_count: int) -> int:
    max_code = flow_count_max_code(bits)
    if max_count <= max_code:
        return max_count
    return max(1, max_code // 8)


def flow_count_log_base(bits: int, max_count: int) -> float:
    max_code = flow_count_max_code(bits)
    first_log_code = flow_count_exact_max(bits, max_count) + 1
    intervals = max_code - first_log_code
    return (max_count / first_log_code) ** (1 / intervals)


def decode_flow_count(code: int, bits: int, max_count: int) -> int:
    if bits == 0:
        return min(code, PINT_MAX_FLOW_COUNT)
    max_code = flow_count_max_code(bits)
    max_count = min(max(max_count, 1), PINT_MAX_FLOW_COUNT)
    code = min(code, max_code)
    if max_count <= max_code:
        return min(code, max_count)
    exact_max = flow_count_exact_max(bits, max_count)
    if code <= exact_max:
        return code
    if code == max_code:
        return max_count
    first_log_code = exact_max + 1
    exponent = code - first_log_code
    value = first_log_code * flow_count_log_base(bits, max_count) ** exponent
    return min(max_count, math.ceil(value))


def encode_flow_count(count: int, bits: int, max_count: int) -> int:
    count = min(count, PINT_MAX_FLOW_COUNT)
    if bits == 0:
        return count
    max_code = flow_count_max_code(bits)
    max_count = min(max(max_count, 1), PINT_MAX_FLOW_COUNT)
    if max_count <= max_code:
        return min(count, max_count)
    exact_max = flow_count_exact_max(bits, max_count)
    if count <= exact_max:
        return count
    if count >= max_count:
        return max_code
    first_log_code = exact_max + 1
    exponent = math.log(count / first_log_code) / math.log(
        flow_count_log_base(bits, max_count)
    )
    code = min(first_log_code + math.ceil(exponent), max_code)
    while code < max_code and decode_flow_count(code, bits, max_count) < count:
        code += 1
    while (
        code > first_log_code
        and decode_flow_count(code - 1, bits, max_count) >= count
    ):
        code -= 1
    return code


def encoded_flow_count_values() -> tuple[int, ...]:
    values = set(
        int(round(value))
        for value in np.geomspace(1, PINT_MAX_FLOW_COUNT, 320)
    )
    for bits in SYNTHETIC_ENCODING_BITS:
        exact_max = flow_count_exact_max(bits, PINT_MAX_FLOW_COUNT)
        values.update((exact_max, exact_max + 1))
    values.update((1, 5, 20, 31, 32, 64, 100, 128, 512, 1024, 8192))
    return tuple(sorted(value for value in values if 1 <= value <= PINT_MAX_FLOW_COUNT))


def flow_count_encoding_rows() -> list[dict[str, float | int | bool]]:
    rows = []
    for bits in SYNTHETIC_ENCODING_BITS:
        max_code = flow_count_max_code(bits)
        exact_max = flow_count_exact_max(bits, PINT_MAX_FLOW_COUNT)
        for true_count in encoded_flow_count_values():
            code = encode_flow_count(true_count, bits, PINT_MAX_FLOW_COUNT)
            decoded = decode_flow_count(code, bits, PINT_MAX_FLOW_COUNT)
            relative_error = (decoded - true_count) / true_count
            rows.append(
                {
                    "bits": bits,
                    "true_count": true_count,
                    "encoded_code": code,
                    "decoded_count": decoded,
                    "exact_max": exact_max,
                    "relative_error": relative_error,
                    "absolute_relative_error": abs(relative_error),
                    "uses_max_code": code == max_code,
                }
            )
    return rows


def utilization_encoding_rows() -> list[dict[str, float | int | bool]]:
    minimum_utilization = 1 / PINT_MAX_CONCURRENT_FLOWS
    utilization_values = np.geomspace(
        minimum_utilization, PINT_MAX_UTILIZATION, 260
    )
    sample_count = 1000
    rows = []
    for bits in SYNTHETIC_ENCODING_BITS:
        max_code = (1 << bits) - 1
        log_base = (
            PINT_MAX_UTILIZATION / minimum_utilization
        ) ** (1 / max_code)
        for value_index, utilization in enumerate(utilization_values):
            exact_power = math.log(
                utilization / minimum_utilization
            ) / math.log(log_base)
            if exact_power >= max_code:
                powers = np.full(sample_count, max_code, dtype=np.int64)
                lower_power = max_code
                upper_power = max_code
                upper_probability = 0.0
            else:
                lower_power = math.floor(exact_power)
                upper_power = math.ceil(exact_power)
                if lower_power == upper_power:
                    powers = np.full(sample_count, lower_power, dtype=np.int64)
                    upper_probability = 0.0
                else:
                    lower_value = minimum_utilization * log_base**lower_power
                    upper_value = minimum_utilization * log_base**upper_power
                    upper_probability = (
                        utilization - lower_value
                    ) / (upper_value - lower_value)
                    rng = np.random.default_rng(
                        73_001 + bits * 10_000 + value_index
                    )
                    powers = np.where(
                        rng.random(sample_count) < upper_probability,
                        upper_power,
                        lower_power,
                    )
            decoded = np.power(log_base, powers) / PINT_MAX_CONCURRENT_FLOWS
            relative_errors = (decoded - utilization) / utilization
            rows.append(
                {
                    "bits": bits,
                    "true_utilization": utilization,
                    "mean_decoded_utilization": float(np.mean(decoded)),
                    "relative_bias": float(np.mean(relative_errors)),
                    "median_absolute_relative_error": float(
                        np.median(np.abs(relative_errors))
                    ),
                    "p95_absolute_relative_error": float(
                        np.quantile(np.abs(relative_errors), 0.95)
                    ),
                    "lower_power": lower_power,
                    "upper_power": upper_power,
                    "upper_probability": upper_probability,
                    "uses_max_code": bool(np.any(powers == max_code)),
                }
            )
    return rows


def field_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "field": "Linear Counting N/S state",
            "selected_bits": SELECTED_SKETCH_BITS,
            "represented_range": "measured empirically",
            "resolution": "one hashed bit per observed flow ID",
            "state_bytes": SELECTED_SKETCH_BITS // 2,
            "notes": "four bitmap banks: active and completed N/S epochs",
        },
        {
            "field": "N and S",
            "selected_bits": SELECTED_FLOW_COUNT_BITS,
            "represented_range": f"0-{PINT_MAX_FLOW_COUNT}",
            "resolution": (
                f"exact through {flow_count_exact_max(SELECTED_FLOW_COUNT_BITS, PINT_MAX_FLOW_COUNT)}, "
                "then conservative logarithmic"
            ),
            "state_bytes": None,
            "notes": "same encoding is used for total and initial-phase counts",
        },
        {
            "field": "U",
            "selected_bits": SELECTED_UTILIZATION_BITS,
            "represented_range": (
                f"{1 / PINT_MAX_CONCURRENT_FLOWS:.8g}-{PINT_MAX_UTILIZATION:g}"
            ),
            "resolution": "autoscaled logarithmic stochastic rounding",
            "state_bytes": None,
            "notes": "full feedback probability p=1",
        },
        {
            "field": "queueDelay",
            "selected_bits": 12,
            "represented_range": "0-262.08 ms",
            "resolution": "64 us",
            "state_bytes": None,
            "notes": "cumulative saturating fixed point",
        },
        {
            "field": "baseRTT",
            "selected_bits": 24,
            "represented_range": "0-16.777215 s",
            "resolution": "1 us",
            "state_bytes": None,
            "notes": "sender telemetry",
        },
        {
            "field": "cwnd",
            "selected_bits": 16,
            "represented_range": "5-bit exponent and 11-bit mantissa",
            "resolution": "floating point",
            "state_bytes": None,
            "notes": "sender telemetry",
        },
        {
            "field": "pathDigest",
            "selected_bits": 32,
            "represented_range": "32-bit rolling fingerprint",
            "resolution": "FNV-style hop update",
            "state_bytes": None,
            "notes": "collisions remain possible and must not be described as impossible",
        },
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(linear_counting_rows()).to_csv(
        OUT_DIR / "linear_counting_samples.csv", index=False
    )
    pd.DataFrame(flow_count_encoding_rows()).to_csv(
        OUT_DIR / "flow_count_encoding.csv", index=False
    )
    pd.DataFrame(utilization_encoding_rows()).to_csv(
        OUT_DIR / "utilization_encoding.csv", index=False
    )
    pd.DataFrame(field_audit_rows()).to_csv(
        OUT_DIR / "field_audit.csv", index=False
    )
    (OUT_DIR / "calibration_metadata.json").write_text(
        json.dumps(
            {
                "experiment": EXPERIMENT,
                "linear_counting_implementation": (
                    "Python vectorized port of PintQueue::mixHash, markFlow, "
                    "and estimateFlowCount; bitmap bits are never set directly "
                    "to a target occupancy"
                ),
                "flow_id_patterns": list(SYNTHETIC_ID_PATTERNS),
                "hash_seed_count": SYNTHETIC_HASH_SEEDS,
                "max_flow_count": SYNTHETIC_MAX_FLOWS,
                "bitmap_bits": list(SYNTHETIC_BITMAP_BITS),
                "encoding_bits": list(SYNTHETIC_ENCODING_BITS),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Generated sensitivity calibration data in {OUT_DIR}")


if __name__ == "__main__":
    main()
