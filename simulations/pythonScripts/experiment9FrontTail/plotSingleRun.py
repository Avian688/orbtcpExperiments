#!/usr/bin/env python

import sys
from pathlib import Path

import pandas as pd

HAS_MATPLOTLIB = True
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
except ModuleNotFoundError:
    HAS_MATPLOTLIB = False
    plt = None
    PdfPages = None

try:
    import scienceplots
    if(HAS_MATPLOTLIB):
        plt.style.use('science')
except ModuleNotFoundError:
    scienceplots = None

if(HAS_MATPLOTLIB):
    plt.rcParams['text.usetex'] = False

METRIC_SPECS = [
    ("goodput.csv", "goodput", "Goodput", "Goodput (Mbps)", lambda x: x / 1000000.0, False),
    ("throughput.csv", "throughput", "Throughput", "Throughput (Mbps)", lambda x: x / 1000000.0, False),
    ("cwnd.csv", "cwnd", "CWND", "CWND (MSS)", lambda x: x / 1448.0, True),
    ("rtt.csv", "rtt", "RTT", "RTT (ms)", lambda x: x * 1000.0, True),
    ("tau.csv", "tau", "Tau", "Tau", lambda x: x * 1000.0, True),
    ("U.csv", "U", "U", "U", lambda x: x * 1000.0, True),
]

def get_module_label(moduleName):
    if("." in moduleName):
        return moduleName.split(".", 1)[1]
    return moduleName

def should_keep_metric_file(metricFileName, moduleName):
    if(".userTerminal[" not in moduleName):
        return False

    if(metricFileName == "goodput.csv"):
        return ".app[" in moduleName

    return ".tcp.conn" in moduleName

def collect_metric_files(runDir, metricSpecs):
    metricFiles = {metricFileName: [] for metricFileName, _, _, _, _, _ in metricSpecs}

    for moduleDir in sorted(runDir.iterdir()):
        if(not moduleDir.is_dir()):
            continue

        moduleName = moduleDir.name
        for metricFileName, _, _, _, _, _ in metricSpecs:
            filePath = moduleDir / metricFileName
            if(filePath.exists() and should_keep_metric_file(metricFileName, moduleName)):
                metricFiles[metricFileName].append((get_module_label(moduleName), filePath))

    return metricFiles

def load_metric_dataframe(filePath, valueColumn):
    try:
        df = pd.read_csv(filePath)
    except Exception:
        return None

    if(df.empty or "time" not in df.columns or valueColumn not in df.columns):
        return None

    return df[["time", valueColumn]].dropna()

def build_plot_title(runDir):
    parts = list(runDir.parts)
    if("csvs" in parts):
        csvIndex = parts.index("csvs")
        return " / ".join(parts[csvIndex + 1:])
    return str(runDir)

if __name__ == "__main__":
    if(len(sys.argv) < 2):
        raise RuntimeError("Usage: plotSingleRun.py <csv-run-directory>")

    if(not HAS_MATPLOTLIB):
        print("matplotlib is not installed; skipping single-run PDF generation.")
        sys.exit(0)

    runDir = Path(sys.argv[1]).resolve()
    if(not runDir.exists()):
        raise RuntimeError("Run directory not found: " + str(runDir))

    metricFiles = collect_metric_files(runDir, METRIC_SPECS)
    activeMetricSpecs = [metricSpec for metricSpec in METRIC_SPECS if metricFiles[metricSpec[0]]]

    if(not activeMetricSpecs):
        print("No user-terminal CSV data found in " + str(runDir))
        sys.exit(0)

    numMetrics = len(activeMetricSpecs)
    numColumns = 2
    numRows = (numMetrics + numColumns - 1) // numColumns
    fig, axes = plt.subplots(numRows, numColumns, figsize=(14, 3.5 * numRows))
    if(hasattr(axes, "flatten")):
        axes = axes.flatten()
    else:
        axes = [axes]

    for axisIndex, metricSpec in enumerate(activeMetricSpecs):
        metricFileName, valueColumn, plotTitle, yLabel, transformFn, stepPlot = metricSpec
        ax = axes[axisIndex]

        for moduleLabel, filePath in metricFiles[metricFileName]:
            df = load_metric_dataframe(filePath, valueColumn)
            if(df is None or df.empty):
                continue

            xValues = df["time"].astype(float)
            yValues = transformFn(df[valueColumn].astype(float))
            if(stepPlot):
                ax.plot(xValues, yValues, drawstyle='steps-post', linewidth=1.2, label=moduleLabel)
            else:
                ax.plot(xValues, yValues, linewidth=1.2, label=moduleLabel)

        ax.grid(True)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(yLabel)
        ax.set_title(plotTitle)
        ax.legend(loc="best", fontsize="x-small")

    for axisIndex in range(len(activeMetricSpecs), len(axes)):
        axes[axisIndex].set_axis_off()

    fig.suptitle(build_plot_title(runDir), fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    with PdfPages("merged_plots.pdf") as pdf:
        pdf.savefig(fig, dpi=300)

    plt.close(fig)
    print("Generated merged_plots.pdf for " + str(runDir))
