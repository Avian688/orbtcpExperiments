# OrbCC Sensitivity Analysis

`experimentSensitivityAnalysis` replaces the broad workload-averaged dynamic
tuning figures with a causal evaluation of Linear Counting, fixed-size PINT
encoding, and feedback frequency.

## Common network setup

All network simulations use a dual-path dumbbell. The active route alternates
between distinct `transitA` and `transitB` router modules every 15 seconds so a
hard handover changes the PINT path digest. Each handover has 45-120 ms of
downtime and installs a matched random path with:

- 50-100 Mbps aggregate bottleneck bandwidth;
- 20-100 ms RTT;
- one current-path BDP of 1448-byte packets at the bottleneck queue;
- distributed RTT without loss, or bottleneck RTT with 0-1% forward loss.

The same ten traces, flow starts, sketch seeds, handover durations, RTTs,
bandwidths, and loss values are reused between variants.
Queue-side stochastic encoding uses a separate RNG stream so it cannot shift
the matched packet-loss realization seen by Exact PINT and OrbCC.

## Subexperiments

1. Representation accuracy uses generated flow IDs with the production hash,
   Linear Counting estimator, N/S mapping, and stochastic U mapping. Bitmap
   occupancy is never filled directly.
2. Feedback sensitivity uses the final OrbCC representation with 64 persistent
   flows and sweeps `p=1/256`, `1/64`, `1/16`, `1/4`, and `1`. Figure 2 reports
   aggregate goodput as a percentage of current capacity over the first ten
   RTTs after reconnection, averaging handovers within each matched run and
   reporting 95% confidence intervals across ten runs. The `p=1` point reuses
   the exactly matched final-OrbCC handover case from Figure 3, so only the 40
   reduced-probability configurations require additional simulations.
3. Handover response uses 64 persistent flows to separate flow-count
   approximation, U encoding, and their combined behavior over the first ten
   RTTs after every reconnection.
4. Final validation compares Exact PINT with the selected OrbCC candidate at
   16, 64, and 128 persistent flows under the two path conditions.

Here, `Exact PINT` means exact flow-count state, exact N/S fields, and exact U
for the mechanisms under test. The other fixed-size sender and path fields are
left unchanged.

The current candidate is configured centrally in
`experimentSensitivityAnalysisSupport.py` as a 4096-bit sketch, 8-bit N/S,
8-bit U, and feedback probability one.

## Running

Run the complete experiment from this directory:

```bash
EXPERIMENT_CORES=30 python3 runExperimentSensitivityAnalysis.py
```

Run one step or a contiguous range with `START_STEP` and `END_STEP`:

```bash
START_STEP=1 END_STEP=1 python3 runExperimentSensitivityAnalysis.py
START_STEP=2 END_STEP=2 EXPERIMENT_CORES=30 python3 runExperimentSensitivityAnalysis.py
START_STEP=5 END_STEP=5 python3 runExperimentSensitivityAnalysis.py
```

The five steps generate inputs, run simulations, export vectors, extract
plotting CSVs, and create figures. Simulation retries, completion markers,
resume behavior, process-group cancellation, and the 9000-second default
timeout come from `raynetExperimentSupport.py`.

Paper figures and final plotted points are written below:

```text
simulations/plots/experimentSensitivityAnalysis/paperPlots/
simulations/plots/experimentSensitivityAnalysis/paperPlots/plot_data/
```

`figure1` covers representation accuracy, `figure2` covers feedback
probability, `figure3` covers handover response, and `figure4` covers final
closed-loop validation. Individual panels and combined multi-panel PDFs are
both generated.
