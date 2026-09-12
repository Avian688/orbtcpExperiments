# Front-drop protocol comparisons

These snapshots compare the existing experiments using FIFO queues that drop
the **oldest queued packet on overflow** (INET's `DropHeadQueue`). "FrontTail"
is the experiment suffix, not an INET queue class or LIFO service policy.

The default protocols are `orbtcp_pint`, `cubic`, `bbr3`, `leocc`, and `satcp`,
restricted to each original experiment's supported matrix. Experiment 3 uses
Cubic, BBRv3 and PINT. Experiments 1-11 and 13 are included; 1 also runs 2.
Experiments 0 and 12 have no PINT setup. Experiment 13 retains its PINT
feedback-probability sweep. Full-INT OrbCC and BBRv1 INIs may be generated as
intermediate inputs, but are not simulated. `--protocols` and
`EXPERIMENT_PROTOCOLS` may select a subset of the supported protocols.

From the orbtcpExperiments directory:

```bash
EXPERIMENT_CORES=30 LEO_SIMULATION_CORES=15 bash simulations/pythonScripts/runAllExperimentFrontTail.sh all
EXPERIMENT_CORES=30 bash simulations/pythonScripts/runAllExperimentFrontTail.sh --plots all
```

Replace `all` with numbers, e.g. `4 5 6`. Each cloned directory also has its own
runner, e.g. `experiment4FrontTail/runExperiment4FrontTail.py`. Run individual
scripts from their directory, as with the original suite. Existing step,
timeout, retry, resume and concurrency settings are inherited. LEO simulations
use `LEO_SIMULATION_CORES` (default 15); other work uses `EXPERIMENT_CORES`.

Generated INIs, scenarios, metadata, CSVs, results, plots and logs use FrontTail
paths. No baseline results are copied. The snapshots preserve the original
workloads and parameters. Plotting uses the supported five-protocol subset;
it does not combine drop-head results with baseline tail-drop results.

`PintFrontTailQueue` inherits the existing PINT C++ implementation and changes
only the overflow dropper to `PacketAtCollectionBeginDropper`. Its compound
interface uses that queue explicitly. An equivalent INT queue/interface is
provided for the generators' intermediate INT configurations. A front-drop
bandwidth-recording queue also preserves experiment-specific signals. Push,
pull, disconnect flushing, telemetry and capacity logic remain inherited.

Push the new NED files in **orbtcp** as well as the experiment files. No new C++
implementation is required. The originals' NED types and scripts are unchanged.

LEO runs load the existing routing corpus from `../experiment8/`; topology
snapshots do not need regeneration merely for a queue-policy comparison.
The original corpus and ground-station inputs must be available as before.
Experiment 8 also retains the `LEO_ROUTING_CORPUS_ROOT` override.

`duplicateFrontTailExperiments.py` creates the snapshots without running a
simulation. It refuses to replace differing existing FrontTail files. Generated
INIs/scenarios need not be committed; the copied generators recreate them.

Validation is static plus isolated generator/selection checks, not a claim of
successful simulation or plot execution.
