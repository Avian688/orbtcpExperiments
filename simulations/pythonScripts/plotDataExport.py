#!/usr/bin/env python3

import json
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_PLOT_DATA_DIR = "plot_data"


def _json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def _serialise_cell(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return json.dumps(value.tolist())
    if isinstance(value, (list, tuple)):
        return json.dumps(value, default=_json_default)
    return value


def export_plot_dataframe(filename, dataframe, base_dir=DEFAULT_PLOT_DATA_DIR, metadata=None):
    """Write final plotted data beside aggregate figures without changing plot logic."""
    out_dir = Path(base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    export_df = dataframe.copy()
    for column in export_df.columns:
        export_df[column] = export_df[column].map(_serialise_cell)

    export_df.to_csv(out_path, index=False)

    if metadata is not None:
        metadata_path = out_path.with_suffix(out_path.suffix + ".metadata.json")
        metadata_path.write_text(json.dumps(metadata, indent=2, default=_json_default))

    print(f"Saved plot data to {out_path}")
    return out_path


def export_heatmap(filename, mean_df, std_df=None, base_dir=DEFAULT_PLOT_DATA_DIR, metadata=None):
    rows = []
    for row_label in mean_df.index:
        for column_label in mean_df.columns:
            row = {
                "row": row_label,
                "series": column_label,
                "mean": mean_df.at[row_label, column_label],
            }
            if std_df is not None:
                row["std"] = std_df.at[row_label, column_label]
            rows.append(row)
    return export_plot_dataframe(filename, pd.DataFrame(rows), base_dir=base_dir, metadata=metadata)


def build_cdf_points(values, bins, denominator=None):
    values = pd.Series(values).dropna().to_numpy()
    counts, base = np.histogram(values, bins=bins)
    cumulative = np.cumsum(counts)
    denom = denominator if denominator is not None else len(values)
    y_percent = cumulative / denom * 100 if denom else np.zeros_like(cumulative, dtype=float)
    return pd.DataFrame({
        "x": base[:-1],
        "y_percent_trials": y_percent,
        "bin_count": counts,
        "cumulative_count": cumulative,
        "sample_count": len(values),
        "denominator": denom,
    })
