# Full-plugin follow-up validation

The PR still contains tests, a benchmark and documentation only. No runtime
optimization is included. Validated PR revision:
`52c8d05cba1b3b40999dbe473030ed3d29045561`.

## What the additional validation found

The original standalone probe registered the four HcPre scalar arguments as
positional-or-keyword arguments. The actual project registers them as
keyword-only arguments. Complete-plugin validation exposed the benchmark's
incorrect positional call; [the retained failure](raw/full-operator-v4/event.log)
shows the actual declaration. The PR now calls `hc_mult`, `hc_sinkhorn_iters`,
`norm_eps` and `hc_eps` by name. The allocation/checking/ACLNN C++ functions in
the earlier probe were unchanged, but that probe's Torch registration was not
an exact copy of the production schema. Earlier measurements remain intact.

## Successful scope

- The real `vllm_ascend.utils.enable_custom_op()` loaded the complete extension.
  No operator registration, test body, oracle or loader import was replaced.
- All **53 tests passed**, with zero failure, error or skip, using the original
  PR test file: [log](raw/full-operator-v5/tests.log),
  [JUnit XML](raw/full-operator-v5/tests.xml).
- The unmodified benchmark entrypoint completed every one of the **28 cases**
  in eager and graph modes, three rounds of 20 warmups plus 50 samples. Every
  eager output matched the earlier unchanged baseline byte for byte; every
  graph output matched eager. All four outputs and input preservation were
  checked. [Eager data](raw/full-operator-v5/event/results.json),
  [graph data](raw/full-operator-v5/graph/results.json).
- Import paths and loaded-library maps show the isolated PR source, real
  extension and private baseline/candidate vendors. The runner records paths
  at exit and invokes the unchanged entrypoints with `runpy`; it does not
  replace functions or registrations.

The isolated Python source was checked out from the PR. The full extension
and direct-kernel library were copied from the existing cloud build, without
changing that checkout or environment. The reused extension was built for the
other mHC expansion contribution, whose runtime changes are outside this
validation scope. The complete HcPre binding section was verified byte for
byte against this PR's source before reuse; its hash, extension hashes and
source revision are in [the provenance](raw/full-plugin-v2/).

## Collection and model limits

Normal nightly collection did **not** pass. Its parent conftest imports FLA,
whose existing wheel build had not completed. Both the missing `fla_npu`
failure and the missing packaged FLA op_api failure are retained under
[full-plugin-v2](raw/full-plugin-v2/tests.log) and
[full-plugin-v3](raw/full-plugin-v3/tests.log). Neither attempt ran test cases.

The successful command uses `--confcutdir` at `singlecard_ops` to exclude those
parent conftest files. It therefore proves real-plugin HcPre execution and
test-body correctness, **not complete nightly integration or full-model
generation**. GLM model generation and A3/A5 hardware remain unverified.
No FLA source or shared environment was modified or replaced with a stub.

## Complete-plugin performance comparison

The excluded accumulator-copy candidate was rerun through the same complete
plugin in fresh-process **ABBA** order: baseline A is `full-operator-v5/graph`,
followed by `full-graph-candidate-a`, `full-graph-candidate-b`, and
`full-graph-baseline-b`. Every process checked for an idle NPU, and every output
was checked byte for byte against the same eager baseline. The common runtime
sets `TASK_QUEUE_ENABLE=1` and uses the same copied extension and PR benchmark.
Unrelated host-side FLA compilation continued; no unrelated NPU process was
observed in the saved guards.

This run has **24/28 faster cases and 4/28 slower cases**, geometric mean speedup
**1.04412**, with the largest slowdown **3.03%**. The earlier standalone graph
comparison has **11/28 faster and 17/28 slower**, geometric mean **1.00351**.
These separate execution setups produce materially different results; they
are not pooled or selectively substituted. The candidate remains excluded
until consistent performance is established. Neither run proves model speedup.

[All 28 cases and p10/p90](comparison.md), [all six round medians](summary.json)
and every warmup/sample in the raw JSON files are retained. Recompute:

```shell
python analyze_full_graph.py raw .
```

## Reproduction and integrity

`raw/run_full_plugin_v2.sh` prepares the isolated checkout and records reused
extension provenance. `raw/run_full_operator_v5.sh` runs successful real-plugin
tests and both benchmark modes. `raw/measure_full_graph.sh` completes ABBA.
Failed earlier scripts and logs remain unchanged, including the incomplete Git
bundle's prerequisite failure. Adapt only workspace paths for another machine.
The five original tests and all numerical thresholds remain unchanged.

The complete text archive has SHA256
`fe019c2f2147163a1695695607c6679a41230559cca70845b30eb3a423e5f8c7`.
The source, hashes, XML and text logs are public; `.pt` outputs remain in the
private cloud workspace, with their hashes and parity results in the raw JSON.
