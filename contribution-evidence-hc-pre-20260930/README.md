# HcPre reduction contribution evidence

This branch preserves the 2026-09-30 audit, all numerical results and all
performance samples for an independent HcPre contribution. The final source
commit is `4fc47457d8a0300f386291afb15fb75a77605410`, based on
`e86df700993c6a83a17306e1320723db86f04691`. Its test/benchmark diff is unchanged
from the tested tree. The HcPre implementation is byte-identical to the tested
`12fd3a90a0895aebbc58926334e9891683c00699` source.

## Accepted contribution

- 48 new nightly numerical cases: hidden sizes 4096/7168, batch shapes 1, 17,
  257 and 3x17, positive/signed inputs and finite Sinkhorn counts 1/3/20.
- Existing 5 cases and thresholds retained; CPU reference defaults to 20.
- Complete HcPre eager/graph benchmark with deterministic inputs, bytewise
  reference comparisons, input-mutation checks and all warmup/measured samples.
- Documentation and DCO sign-off; no operator or model implementation change.

## Verified and unverified scope

Ascend 910B3 physical device 3 / logical device 0, CANN 9.1.0,
torch 2.10.0+cpu, torch_npu 2.10.0.post4, Python 3.12, GCC 13.

The final unchanged upstream HcPre package passed **53/53 test bodies** through
a standalone ACLNN harness: [log](raw/final-upstream-tests/tests.log),
[JUnit XML](raw/final-upstream-tests/tests.xml). The harness extracts the upstream
allocation/checking/ACLNN binding functions unchanged, removes only full-plugin
loading imports and uses the original test bodies/oracle. This is full-operator
NPU validation, not a full vLLM installation, full-model test or A3/A5 result.
[Loaded library paths](raw/final-upstream-tests/loaded-libraries.txt) prove the
private baseline vendor was loaded. The final device snapshot was idle.

`bash format.sh ci`, the repository's complete manual lint suite, passed.
Source hashes and package/kernel hashes are preserved under `raw/`.

## Rejected optimization and retained failures

`rejected-kernel.patch` removes an accumulator seed copy for aligned reductions.
It compiled on both arms, passed the 21-case intermediate suite on each arm,
and matched all four outputs bitwise for all 28 benchmark cases across eager
and graph execution. It is **not in the PR**: graph performance improved in
11/28 cases and slowed down in 17/28; geometric mean speedup was **1.00351**.
Single-token gains did not establish a broadly useful improvement.

[Complete comparison](comparison.md) includes every slowdown and p10/p90.
[summary.json](summary.json) retains all six round medians per arm, eager/graph
wall measurements and pooled statistics. Raw per-round samples remain in every
`raw/*/data/results.json`; no best-round or best-case selection is made.

The initial strong signed-input CPU-oracle suite yielded **14 pass / 7 fail on
the unmodified baseline**. [Failure log](raw/baseline-tests/tests.log),
[XML](raw/baseline-tests/tests.xml) and
[exact fixture source](raw/test_npu_hc_pre_strong_v1.py) are retained.
No accuracy threshold was loosened. The accepted signed regression fixture
retains the existing `1/fan_in` weight scale. The larger `1/sqrt(fan_in)` signed
benchmark fixtures remain in all A/B matrices; baseline parity does not prove
their CPU accuracy. One separate launch was blocked by the busy-device guard
before any NPU work; `raw/baseline-tests-v2/` preserves that snapshot/exit.

Eager measurements overlapped unrelated host-side FLA compilation and have
substantial noise (10/28 faster, 18/28 slower; geomean speedup 0.96909). No
unrelated NPU workload was observed by the device guards. Graphs amortize host
launch cost over 20 HcPre calls; capture/setup is excluded, and event/graph wall
times are reported per operator. Graph wall time is not eager invocation latency.
Neither measurement establishes an end-to-end model speedup.

## Reproduction

Use an existing supported Ascend environment without changing shared packages.
Clone the source and make the frozen source archive used by the private build:

```shell
git clone https://github.com/vllm-project/vllm-ascend.git vllm-ascend
git -C vllm-ascend archive 12fd3a90a0895aebbc58926334e9891683c00699 \
    csrc .gitmodules | gzip > upstream-csrc.tar.gz
cp rejected-kernel.patch candidate.patch
```

The private-build script explicitly uses CANN 9.1 and an existing Torch/NPU
environment. Adapt its three workspace paths and existing Catlass include path
to the machine. Build flags are identical across arms; package vendor names and
installation directories are separate. Do not install either into shared OPP.

Run the final upstream test file or the documented benchmark with an installed
full plugin. For the exact standalone reproduction, use `raw/probe.py` and
`raw/run_variant.sh`; generated `raw/probe.cpp` shows the unchanged binding.
`raw/validate_and_measure.sh` records eager ABBA, and `raw/measure_graph.sh`
records graph ABBA. Each process checks/saves the device state and library maps.
The older eager harness/benchmark source is preserved with `_event_v1` suffixes.

Run `python analyze.py` to regenerate summary/comparison from the raw JSONs.
The deterministic `.pt` output tensors and both installed packages remain in
the private cloud directory; their hashes and bytewise validation outcomes are
in the public evidence. No competition code was copied or relicensed.

## Archive integrity

- Initial complete text evidence archive SHA256:
  `579238f1d0822a587481dc696fcee430510f2af4242729587a0a70460305d005`.
- Final 53-case results archive SHA256:
  `456dccdd829d9af22bd77630fad1d418d4ceaa497f48d1ab84793abede2d8354`.

Both hashes matched between cloud and local copies. [Source audit](source-audit.md)
records provenance, licensing, real callers, active/merged PR overlap and limits.
